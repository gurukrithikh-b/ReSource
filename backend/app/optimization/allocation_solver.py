"""
Multi-Point Resource Allocation Solver — Phase 4, Step 1
=========================================================
Uses Google OR-Tools (GLOP / CBC continuous LP) to find the globally-optimal
distribution of food surplus across multiple community demand listings.

────────────────────────────────────────────────────────────────────────────
WHY THIS GOES BEYOND PHASE 3.3 MATCHING
────────────────────────────────────────────────────────────────────────────
Phase 3.3 evaluates every (surplus, demand) pair *independently* and ranks
them.  It cannot answer: "Given Hotel A has 500 kg AND Restaurant B has
300 kg, and NGO A needs 400 kg, NGO B needs 350 kg, and Shelter C needs
250 kg — what is the *globally best* distribution that maximises total food
rescued across all suppliers and receivers simultaneously?"

This solver answers that question via a Linear Programme (LP):

  decision variable:  x[i,j] ∈ ℝ⁺   — kg allocated from surplus i to demand j

  subject to:
    Σ_j  x[i,j]  ≤  remaining_qty[i]     ∀ i  (supply constraint)
    Σ_i  x[i,j]  ≤  needed_qty[j]        ∀ j  (demand constraint)
            x[i,j]  ≥  0                  ∀ i,j (non-negativity)
    x[i,j]  =  0  if pair (i,j) not viable (compatibility constraint)

  maximise:
    Σ_{i,j}  x[i,j] × obj_coeff[i,j]

────────────────────────────────────────────────────────────────────────────
OBJECTIVE FUNCTION — documented coefficient construction
────────────────────────────────────────────────────────────────────────────
The coefficient attached to each decision variable x[i,j] combines three
terms so that the solver balances *quantity*, *match quality*, and *distance*:

  obj_coeff[i,j] = w_qty      (always 1.0  — primary: maximise allocation)
                 + w_score × normalised_score[i,j]   (match quality bonus)
                 - w_dist  × normalised_dist[i,j]    (distance penalty)

  where:
    normalised_score = match_score / 100          ∈ [0, 1]
    normalised_dist  = min(distance_km, D_MAX) / D_MAX  ∈ [0, 1]
                       (0.5 when distance unknown)

  weights (sum to meaningful magnitudes):
    w_qty   = 1.0   — each kg allocated contributes 1.0 to the objective
    w_score = 0.2   — up to +0.20 bonus per kg for a perfect (100) match
    w_dist  = 0.1   — up to −0.10 penalty per kg for maximum distance

  Rationale:
    - A pair with match_score=100 and dist=0 earns 1.20 per kg.
    - A pair with match_score=0  and dist=50 km earns 0.90 per kg.
    - Neither bonus/penalty can ever dominate quantity (their max swing is
      only ±30% of the base quantity coefficient).
    - The coefficient is always positive for any viable pair, so the solver
      will always prefer allocating over leaving food unallocated.

────────────────────────────────────────────────────────────────────────────
SOLVER CONFIGURATION
────────────────────────────────────────────────────────────────────────────
OR-Tools GLOP (Revised Simplex LP) is used because:
  - All decision variables are continuous (kg can be fractional for food).
  - GLOP is deterministic, fast, and guaranteed to find the global optimum.
  - If integer allocations are ever needed, switch to CBC (MILP).

A 30-second wall-clock time limit is imposed to prevent unbounded runs on
very large problem instances.

────────────────────────────────────────────────────────────────────────────
PUBLIC API SURFACE
────────────────────────────────────────────────────────────────────────────
  SurplusInput          — describes one surplus listing
  DemandInput           — describes one demand listing
  ViableMatch           — a pre-screened Phase-3.3-viable (i,j) pair
  SolverInput           — full problem specification
  AllocationOutput      — one resolved x[i,j] > 0 allocation
  SolverOutput          — full result including summary statistics

  AllocationSolver.solve(SolverInput) → SolverOutput
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Objective-function tuning constants
# ---------------------------------------------------------------------------
W_QTY   = 1.0   # weight on kg allocated (primary objective)
W_SCORE = 0.2   # weight on normalised match score bonus (0–1)
W_DIST  = 0.1   # weight on normalised distance penalty  (0–1)
D_MAX   = 50.0  # km at which distance penalty is maximised (matches Phase 3.3)

# Solver wall-clock time limit (seconds)
SOLVER_TIME_LIMIT_MS = 30_000

# Minimum allocated quantity to report (avoids floating-point noise)
MIN_ALLOC_KG = 0.001


# ---------------------------------------------------------------------------
# Input dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SurplusInput:
    """
    Describes one surplus resource listing passed into the solver.

    Fields mirror the SurplusListing DB model; only the fields the
    optimizer needs are included — no SQLAlchemy objects cross this boundary.
    """
    id: str
    remaining_quantity: float    # kg available (must be > 0 to be usable)
    expires_at: datetime         # used to verify non-expiry; pre-screen only
    storage_condition: str       # "AMBIENT" | "REFRIGERATED" | "FROZEN"
    supplier_lat: Optional[float] = None
    supplier_lon: Optional[float] = None
    category_id: Optional[str]  = None
    category_name: Optional[str] = None
    title: Optional[str]        = None


@dataclass
class DemandInput:
    """
    Describes one open demand listing passed into the solver.
    """
    id: str
    requested_quantity: float
    fulfilled_quantity: float    # already satisfied; solver works on the remainder
    required_by: datetime
    urgency_level: str           # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    storage_capacity: str
    receiver_lat: Optional[float] = None
    receiver_lon: Optional[float] = None
    category_id: Optional[str]  = None
    category_name: Optional[str] = None
    title: Optional[str]        = None

    @property
    def needed_quantity(self) -> float:
        """Remaining kg the demand still needs."""
        return max(0.0, self.requested_quantity - self.fulfilled_quantity)


@dataclass
class ViableMatch:
    """
    A (surplus_id, demand_id) pair that has already passed Phase 3.3
    viability screening.  The solver only creates decision variables for
    entries in this list.

    `match_score`  : Phase-3.3 overall score, 0–100.
    `distance_km`  : Haversine km; None if coordinates unavailable.
    """
    surplus_id:  str
    demand_id:   str
    match_score: float
    distance_km: Optional[float] = None


@dataclass
class SolverInput:
    """
    Complete problem specification for one optimisation run.

    `surplus_items`  : all available surplus listings (filtered for qty > 0)
    `demand_items`   : all open demand listings (filtered for needed_qty > 0)
    `viable_matches` : pre-screened Phase-3.3-viable (surplus_id, demand_id) pairs
                       — pairs NOT in this list receive x[i,j] = 0 implicitly.

    The caller is responsible for pre-screening; the solver trusts this list.
    """
    surplus_items:  List[SurplusInput]  = field(default_factory=list)
    demand_items:   List[DemandInput]   = field(default_factory=list)
    viable_matches: List[ViableMatch]   = field(default_factory=list)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

class AllocationStatus(str, Enum):
    ALLOCATED          = "ALLOCATED"           # x[i,j] satisfies full demand need
    PARTIALLY_ALLOCATED = "PARTIALLY_ALLOCATED" # x[i,j] > 0 but < demand needed


@dataclass
class AllocationOutput:
    """
    One resolved allocation: surplus i supplies x[i,j] kg to demand j.

    This maps directly to a future Allocation DB record.
    """
    surplus_id:        str
    demand_id:         str
    allocated_quantity: float
    match_score:       float
    distance_km:       Optional[float]
    status:            AllocationStatus


class SolverStatus(str, Enum):
    OPTIMAL    = "OPTIMAL"     # globally-optimal solution found
    FEASIBLE   = "FEASIBLE"    # feasible but may not be optimal (time limit hit)
    INFEASIBLE = "INFEASIBLE"  # problem has no feasible solution (shouldn't happen for LP≥0)
    NO_DATA    = "NO_DATA"     # no surplus, demand, or viable matches provided
    UNAVAILABLE = "UNAVAILABLE" # OR-Tools not installed


@dataclass
class SolverOutput:
    """
    Complete result of one optimisation run.

    Summary statistics give callers a human-readable audit without
    iterating over every AllocationOutput.
    """
    # ---- required field first (no default) ---
    status: SolverStatus

    # ---- quantities (all in kg) ---
    total_supply_available: float = 0.0   # Σ remaining_quantity across all surplus
    total_demand_requested: float = 0.0   # Σ needed_quantity across all demands
    total_allocated:        float = 0.0   # Σ x[i,j] for all (i,j)
    total_unallocated:      float = 0.0   # total_supply_available − total_allocated
    total_unmet_demand:     float = 0.0   # total_demand_requested − total_allocated

    # ---- allocation breakdown ---
    num_allocations:             int = 0  # pairs with x[i,j] > MIN_ALLOC_KG
    num_demands_fully_satisfied: int = 0
    num_demands_partially_satisfied: int = 0
    num_demands_unsatisfied:     int = 0

    # ---- solver metadata ---
    objective_value:       float = 0.0   # raw OR-Tools objective (for debugging)
    solver_wall_time_ms:   float = 0.0

    # ---- individual allocations ---
    allocations: List[AllocationOutput] = field(default_factory=list)

    # ---- diagnostics ---
    message: str = ""


# ---------------------------------------------------------------------------
# Main solver class
# ---------------------------------------------------------------------------

class AllocationSolver:
    """
    Wraps OR-Tools GLOP LP solver to produce globally-optimal multi-point
    food resource allocations.

    Usage::

        from app.optimization.allocation_solver import (
            AllocationSolver, SolverInput, SurplusInput, DemandInput, ViableMatch
        )

        solver = AllocationSolver()
        result = solver.solve(SolverInput(
            surplus_items=[...],
            demand_items=[...],
            viable_matches=[...],
        ))
        print(result.status, result.total_allocated)
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        try:
            from ortools.linear_solver import pywraplp  # noqa: F401
            self._available = True
            self._use_scipy = False
        except (ImportError, Exception):
            try:
                import scipy.optimize  # noqa: F401
                self._available = True
                self._use_scipy = True
                logger.info("OR-Tools not available or failed to load. Using scipy.optimize.linprog fallback.")
            except ImportError:
                self._available = False
                self._use_scipy = False
                logger.warning(
                    "Neither OR-Tools nor SciPy found. AllocationSolver will return UNAVAILABLE status."
                )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def solve(self, problem: SolverInput) -> SolverOutput:
        """
        Solve the multi-point allocation LP and return a SolverOutput.

        This method is pure-function: it does NOT write to the database.
        Callers (future API endpoints) are responsible for persisting results.

        Steps:
          1. Validate / filter input.
          2. Build OR-Tools GLOP model (or SciPy HiGHS fallback).
          3. Add decision variables (one per viable pair).
          4. Add supply + demand constraints.
          5. Set objective coefficients.
          6. Solve.
          7. Extract and return SolverOutput.
        """
        # ---- fast-path: nothing to do --------------------------------------
        early = self._check_early_exit(problem)
        if early is not None:
            return early

        if not self._available:
            return SolverOutput(
                status=SolverStatus.UNAVAILABLE,
                message="Neither OR-Tools nor SciPy LP solvers are installed.",
            )

        if getattr(self, "_use_scipy", False):
            return self._build_and_solve_scipy(problem)

        # ---- build and solve with OR-Tools --------------------------------
        return self._build_and_solve(problem)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_early_exit(problem: SolverInput) -> Optional[SolverOutput]:
        """Return a NO_DATA SolverOutput for trivially empty problems."""
        sup_qty  = sum(s.remaining_quantity for s in problem.surplus_items if s.remaining_quantity > 0)
        dem_qty  = sum(d.needed_quantity    for d in problem.demand_items  if d.needed_quantity > 0)
        n_viable = len(problem.viable_matches)

        def _no_data(msg: str) -> SolverOutput:
            return SolverOutput(
                status=SolverStatus.NO_DATA,
                total_supply_available=sup_qty,
                total_demand_requested=dem_qty,
                total_unallocated=sup_qty,
                total_unmet_demand=dem_qty,
                message=msg,
            )

        if not problem.surplus_items:
            return _no_data("No surplus listings provided.")
        if not problem.demand_items:
            return _no_data("No demand listings provided.")
        if sup_qty == 0:
            return _no_data("All surplus listings have zero remaining quantity.")
        if dem_qty == 0:
            return _no_data("All demand listings are already fully fulfilled.")
        if n_viable == 0:
            return _no_data("No viable surplus\u2013demand pairs. No compatible matches exist.")

        return None  # proceed to full LP

    def _objective_coeff(self, match: ViableMatch) -> float:
        """
        Compute the objective coefficient for decision variable x[i,j].

        See module docstring for full derivation.

        coefficient = W_QTY
                    + W_SCORE × (match_score / 100)
                    - W_DIST  × (min(dist, D_MAX) / D_MAX)

        Result is always > 0 for any viable pair, ensuring the solver
        always prefers allocating over not allocating.
        """
        norm_score = match.match_score / 100.0  # ∈ [0, 1]

        if match.distance_km is None:
            norm_dist = 0.5   # neutral (unknown location)
        else:
            norm_dist = min(match.distance_km, D_MAX) / D_MAX  # ∈ [0, 1]

        coeff = W_QTY + W_SCORE * norm_score - W_DIST * norm_dist
        # Guarantee non-negative coefficient (worst case: 1.0 + 0.0 - 0.1 = 0.90)
        return max(coeff, 1e-6)

    def _build_and_solve(self, problem: SolverInput) -> SolverOutput:
        """Construct the OR-Tools LP, solve it, extract results."""
        from ortools.linear_solver import pywraplp

        # ---- index structures -----------------------------------------------
        surplus_map: Dict[str, SurplusInput] = {s.id: s for s in problem.surplus_items}
        demand_map:  Dict[str, DemandInput]  = {d.id: d for d in problem.demand_items}

        # Only keep viable pairs whose surplus AND demand are actually present
        # and have positive quantities (double-safety filter)
        pairs: List[ViableMatch] = [
            m for m in problem.viable_matches
            if  m.surplus_id in surplus_map
            and m.demand_id  in demand_map
            and surplus_map[m.surplus_id].remaining_quantity > 0
            and demand_map[m.demand_id].needed_quantity       > 0
        ]

        if not pairs:
            total_sup = sum(s.remaining_quantity for s in problem.surplus_items)
            total_dem = sum(d.needed_quantity    for d in problem.demand_items)
            return SolverOutput(
                status=SolverStatus.NO_DATA,
                message="No viable pairs with positive quantities remain after filtering.",
                total_supply_available=total_sup,
                total_demand_requested=total_dem,
                total_unallocated=total_sup,
                total_unmet_demand=total_dem,
            )

        # ---- create solver --------------------------------------------------
        # GLOP: Google's revised simplex for continuous LP — deterministic, fast
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if solver is None:
            # Fall back to CBC if GLOP is somehow unavailable
            solver = pywraplp.Solver.CreateSolver("CBC")
        if solver is None:
            return SolverOutput(
                status=SolverStatus.UNAVAILABLE,
                message="Failed to create OR-Tools solver (GLOP/CBC both unavailable).",
            )

        solver.SetTimeLimit(SOLVER_TIME_LIMIT_MS)

        # ---- decision variables  x[i,j] ∈ [0, min(supply_i, need_j)] -------
        # Bounding each variable tightly reduces the feasible region and
        # improves solver performance.
        variables: Dict[Tuple[str, str], pywraplp.Variable] = {}
        for m in pairs:
            sup = surplus_map[m.surplus_id]
            dem = demand_map[m.demand_id]
            ub = min(sup.remaining_quantity, dem.needed_quantity)
            var = solver.NumVar(0.0, ub, f"x_{m.surplus_id}_{m.demand_id}")
            variables[(m.surplus_id, m.demand_id)] = var

        # ---- supply constraints:  Σ_j x[i,j] ≤ remaining_qty[i]  ----------
        for s in problem.surplus_items:
            if s.remaining_quantity <= 0:
                continue
            related = [
                variables[(m.surplus_id, m.demand_id)]
                for m in pairs if m.surplus_id == s.id
            ]
            if related:
                ct = solver.Constraint(-solver.infinity(), s.remaining_quantity,
                                       f"supply_{s.id}")
                for v in related:
                    ct.SetCoefficient(v, 1.0)

        # ---- demand constraints:  Σ_i x[i,j] ≤ needed_qty[j]  -------------
        for d in problem.demand_items:
            needed = d.needed_quantity
            if needed <= 0:
                continue
            related = [
                variables[(m.surplus_id, m.demand_id)]
                for m in pairs if m.demand_id == d.id
            ]
            if related:
                ct = solver.Constraint(-solver.infinity(), needed,
                                       f"demand_{d.id}")
                for v in related:
                    ct.SetCoefficient(v, 1.0)

        # ---- objective function:  maximise Σ coeff[i,j] × x[i,j]  ---------
        objective = solver.Objective()
        match_by_pair = {(m.surplus_id, m.demand_id): m for m in pairs}
        for (sid, did), var in variables.items():
            coeff = self._objective_coeff(match_by_pair[(sid, did)])
            objective.SetCoefficient(var, coeff)
        objective.SetMaximization()

        # ---- solve ----------------------------------------------------------
        result_status = solver.Solve()
        wall_ms = solver.wall_time()

        if result_status == pywraplp.Solver.OPTIMAL:
            status = SolverStatus.OPTIMAL
        elif result_status == pywraplp.Solver.FEASIBLE:
            status = SolverStatus.FEASIBLE
        elif result_status == pywraplp.Solver.INFEASIBLE:
            return SolverOutput(
                status=SolverStatus.INFEASIBLE,
                message="LP is infeasible — this should not occur for a non-negative LP. "
                        "Check input data.",
                solver_wall_time_ms=wall_ms,
            )
        else:
            return SolverOutput(
                status=SolverStatus.INFEASIBLE,
                message=f"OR-Tools returned unexpected status code {result_status}.",
                solver_wall_time_ms=wall_ms,
            )

        # ---- extract solution  ----------------------------------------------
        allocations: List[AllocationOutput] = []
        demand_allocated: Dict[str, float]  = {d.id: 0.0 for d in problem.demand_items}

        for (sid, did), var in variables.items():
            qty = var.solution_value()
            if qty < MIN_ALLOC_KG:
                continue  # floating-point noise — skip

            m = match_by_pair[(sid, did)]
            demand_allocated[did] = demand_allocated.get(did, 0.0) + qty

            allocations.append(AllocationOutput(
                surplus_id=sid,
                demand_id=did,
                allocated_quantity=round(qty, 4),
                match_score=m.match_score,
                distance_km=m.distance_km,
                status=AllocationStatus.ALLOCATED,   # refined below
            ))

        # Refine per-allocation status and compute demand satisfaction counts
        total_allocated = 0.0
        for alloc in allocations:
            dem = demand_map[alloc.demand_id]
            needed = dem.needed_quantity
            total_for_this_demand = demand_allocated.get(alloc.demand_id, 0.0)
            if total_for_this_demand >= needed - MIN_ALLOC_KG:
                alloc.status = AllocationStatus.ALLOCATED
            else:
                alloc.status = AllocationStatus.PARTIALLY_ALLOCATED
            total_allocated += alloc.allocated_quantity

        total_supply   = sum(s.remaining_quantity for s in problem.surplus_items)
        total_demand   = sum(d.needed_quantity    for d in problem.demand_items)

        fully_sat   = sum(
            1 for d in problem.demand_items
            if demand_allocated.get(d.id, 0.0) >= d.needed_quantity - MIN_ALLOC_KG
            and d.needed_quantity > 0
        )
        partially_sat = sum(
            1 for d in problem.demand_items
            if MIN_ALLOC_KG <= demand_allocated.get(d.id, 0.0) < d.needed_quantity - MIN_ALLOC_KG
            and d.needed_quantity > 0
        )
        unsatisfied = sum(
            1 for d in problem.demand_items
            if demand_allocated.get(d.id, 0.0) < MIN_ALLOC_KG
            and d.needed_quantity > 0
        )

        return SolverOutput(
            status=status,
            total_supply_available=round(total_supply, 4),
            total_demand_requested=round(total_demand, 4),
            total_allocated=round(total_allocated, 4),
            total_unallocated=round(total_supply - total_allocated, 4),
            total_unmet_demand=round(total_demand - total_allocated, 4),
            num_allocations=len(allocations),
            num_demands_fully_satisfied=fully_sat,
            num_demands_partially_satisfied=partially_sat,
            num_demands_unsatisfied=unsatisfied,
            objective_value=round(solver.Objective().Value(), 6),
            solver_wall_time_ms=wall_ms,
            allocations=allocations,
            message=f"Solved to {status.value} optimality.",
        )

    def _build_and_solve_scipy(self, problem: SolverInput) -> SolverOutput:
        """Fallback solver using scipy.optimize.linprog with HiGHS solver engine."""
        import time
        from scipy.optimize import linprog

        t0 = time.time()
        surplus_map: Dict[str, SurplusInput] = {s.id: s for s in problem.surplus_items}
        demand_map:  Dict[str, DemandInput]  = {d.id: d for d in problem.demand_items}

        pairs: List[ViableMatch] = [
            m for m in problem.viable_matches
            if  m.surplus_id in surplus_map
            and m.demand_id  in demand_map
            and surplus_map[m.surplus_id].remaining_quantity > 0
            and demand_map[m.demand_id].needed_quantity       > 0
        ]

        if not pairs:
            total_sup = sum(s.remaining_quantity for s in problem.surplus_items)
            total_dem = sum(d.needed_quantity    for d in problem.demand_items)
            return SolverOutput(
                status=SolverStatus.NO_DATA,
                message="No viable pairs with positive quantities remain after filtering.",
                total_supply_available=total_sup,
                total_demand_requested=total_dem,
                total_unallocated=total_sup,
                total_unmet_demand=total_dem,
            )

        c = [-self._objective_coeff(m) for m in pairs]

        active_surpluses = [s for s in problem.surplus_items if s.remaining_quantity > 0]
        active_demands   = [d for d in problem.demand_items if d.needed_quantity > 0]

        A_ub = []
        b_ub = []

        for s in active_surpluses:
            row = [1.0 if m.surplus_id == s.id else 0.0 for m in pairs]
            if any(row):
                A_ub.append(row)
                b_ub.append(s.remaining_quantity)

        for d in active_demands:
            row = [1.0 if m.demand_id == d.id else 0.0 for m in pairs]
            if any(row):
                A_ub.append(row)
                b_ub.append(d.needed_quantity)

        bounds = [
            (0.0, min(surplus_map[m.surplus_id].remaining_quantity, demand_map[m.demand_id].needed_quantity))
            for m in pairs
        ]

        res = linprog(c, A_ub=A_ub if A_ub else None, b_ub=b_ub if b_ub else None, bounds=bounds, method="highs")

        wall_ms = (time.time() - t0) * 1000.0

        if not res.success:
            return SolverOutput(
                status=SolverStatus.INFEASIBLE,
                message=f"SciPy LP solver failed: {res.message}",
                solver_wall_time_ms=wall_ms,
            )

        status = SolverStatus.OPTIMAL
        allocations: List[AllocationOutput] = []
        demand_allocated: Dict[str, float] = {d.id: 0.0 for d in problem.demand_items}

        for k, m in enumerate(pairs):
            qty = float(res.x[k])
            if qty < MIN_ALLOC_KG:
                continue

            demand_allocated[m.demand_id] = demand_allocated.get(m.demand_id, 0.0) + qty
            allocations.append(AllocationOutput(
                surplus_id=m.surplus_id,
                demand_id=m.demand_id,
                allocated_quantity=round(qty, 4),
                match_score=m.match_score,
                distance_km=m.distance_km,
                status=AllocationStatus.ALLOCATED,
            ))

        total_allocated = 0.0
        for alloc in allocations:
            dem = demand_map[alloc.demand_id]
            needed = dem.needed_quantity
            total_for_this_demand = demand_allocated.get(alloc.demand_id, 0.0)
            if total_for_this_demand >= needed - MIN_ALLOC_KG:
                alloc.status = AllocationStatus.ALLOCATED
            else:
                alloc.status = AllocationStatus.PARTIALLY_ALLOCATED
            total_allocated += alloc.allocated_quantity

        total_supply = sum(s.remaining_quantity for s in problem.surplus_items)
        total_demand = sum(d.needed_quantity for d in problem.demand_items)

        fully_sat = sum(
            1 for d in problem.demand_items
            if demand_allocated.get(d.id, 0.0) >= d.needed_quantity - MIN_ALLOC_KG
            and d.needed_quantity > 0
        )
        partially_sat = sum(
            1 for d in problem.demand_items
            if MIN_ALLOC_KG <= demand_allocated.get(d.id, 0.0) < d.needed_quantity - MIN_ALLOC_KG
            and d.needed_quantity > 0
        )
        unsatisfied = sum(
            1 for d in problem.demand_items
            if demand_allocated.get(d.id, 0.0) < MIN_ALLOC_KG
            and d.needed_quantity > 0
        )

        return SolverOutput(
            status=status,
            total_supply_available=round(total_supply, 4),
            total_demand_requested=round(total_demand, 4),
            total_allocated=round(total_allocated, 4),
            total_unallocated=round(total_supply - total_allocated, 4),
            total_unmet_demand=round(total_demand - total_allocated, 4),
            num_allocations=len(allocations),
            num_demands_fully_satisfied=fully_sat,
            num_demands_partially_satisfied=partially_sat,
            num_demands_unsatisfied=unsatisfied,
            objective_value=round(-float(res.fun), 6),
            solver_wall_time_ms=wall_ms,
            allocations=allocations,
            message=f"Solved to {status.value} optimality via SciPy HiGHS.",
        )


# ---------------------------------------------------------------------------
# Module-level singleton (mirrors Phase 3.3 / 3.2 pattern)
# ---------------------------------------------------------------------------
allocation_solver = AllocationSolver()
