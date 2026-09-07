"""
Optimization Schemas — Phase 4, Step 1
=======================================
Pydantic request/response models for the allocation solver.
Mirrors the solver's internal dataclasses but adds field-level
validation and OpenAPI documentation metadata for future endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.optimization.allocation_solver import AllocationStatus, SolverStatus


# ---------------------------------------------------------------------------
# Per-allocation output
# ---------------------------------------------------------------------------

class AllocationOutputSchema(BaseModel):
    """
    One resolved allocation: surplus_i supplies `allocated_quantity` kg to demand_j.

    `status`:
      - ALLOCATED          — the allocation satisfies the full remaining demand need
      - PARTIALLY_ALLOCATED — x[i,j] > 0 but the demand remains partially unmet
    """
    surplus_id:         str   = Field(..., description="ID of the contributing surplus listing")
    demand_id:          str   = Field(..., description="ID of the receiving demand listing")
    allocated_quantity: float = Field(..., ge=0, description="kg allocated from surplus to demand")
    match_score:        float = Field(..., ge=0, le=100, description="Phase-3.3 compatibility score (0–100)")
    distance_km:        Optional[float] = Field(None, description="Haversine km; null when coordinates unavailable")
    status:             AllocationStatus

    # Enriched display fields (Phase 4.2 & 4.4)
    surplus_title: Optional[str] = Field(None, description="Title of the surplus listing")
    surplus_unit:  Optional[str] = Field(None, description="Unit of measurement for surplus")
    supplier_name: Optional[str] = Field(None, description="Name of the supplier organization")
    supplier_lat:  Optional[float] = Field(None, description="Latitude of the supplier organization")
    supplier_lon:  Optional[float] = Field(None, description="Longitude of the supplier organization")
    demand_title:  Optional[str] = Field(None, description="Title of the demand listing")
    demand_unit:   Optional[str] = Field(None, description="Unit of measurement for demand")
    receiver_name: Optional[str] = Field(None, description="Name of the receiver organization")
    receiver_lat:  Optional[float] = Field(None, description="Latitude of the receiver organization")
    receiver_lon:  Optional[float] = Field(None, description="Longitude of the receiver organization")
    category_name: Optional[str] = Field(None, description="Category name of the resource")



# ---------------------------------------------------------------------------
# Full solver result
# ---------------------------------------------------------------------------

class OptimizationResultSchema(BaseModel):
    """
    Complete result of one multi-point allocation optimisation run.

    The solver maximises:
        Σ_{i,j}  x[i,j] × (1.0 + 0.2 × score_norm[i,j] − 0.1 × dist_norm[i,j])

    subject to:
        supply constraints  — Σ_j x[i,j] ≤ remaining_qty[i]
        demand constraints  — Σ_i x[i,j] ≤ needed_qty[j]
        non-negativity      — x[i,j] ≥ 0
        compatibility       — x[i,j] = 0 for non-viable (Phase-3.3) pairs
    """
    status: SolverStatus = Field(description="OPTIMAL | FEASIBLE | INFEASIBLE | NO_DATA | UNAVAILABLE")

    # quantities
    total_supply_available: float = Field(0.0, ge=0, description="Total kg available across all surplus listings")
    total_demand_requested: float = Field(0.0, ge=0, description="Total kg still needed across all demand listings")
    total_allocated:        float = Field(0.0, ge=0, description="Total kg the solver allocated (global optimum)")
    total_unallocated:      float = Field(0.0, ge=0, description="Surplus kg left unallocated after optimisation")
    total_unmet_demand:     float = Field(0.0, ge=0, description="Demand kg that could not be satisfied")

    # demand satisfaction counts
    num_allocations:                int = Field(0, ge=0)
    num_demands_fully_satisfied:    int = Field(0, ge=0)
    num_demands_partially_satisfied: int = Field(0, ge=0)
    num_demands_unsatisfied:        int = Field(0, ge=0)

    # solver metadata
    objective_value:     float = Field(0.0, description="Raw OR-Tools objective value (for debugging)")
    solver_wall_time_ms: float = Field(0.0, ge=0, description="Solver wall-clock time in milliseconds")

    # individual allocations
    allocations: List[AllocationOutputSchema] = Field(default_factory=list)

    message: str = ""


class OptimizationSummarySchema(BaseModel):
    """
    Summary view of multi-point allocation optimization for dashboard widgets.
    """
    status: SolverStatus = Field(description="OPTIMAL | FEASIBLE | INFEASIBLE | NO_DATA | UNAVAILABLE")
    total_supply_available: float = Field(0.0, ge=0)
    total_demand_requested: float = Field(0.0, ge=0)
    total_allocated:        float = Field(0.0, ge=0)
    total_unallocated:      float = Field(0.0, ge=0)
    total_unmet_demand:     float = Field(0.0, ge=0)
    num_allocations:                int = Field(0, ge=0)
    num_demands_fully_satisfied:    int = Field(0, ge=0)
    num_demands_partially_satisfied: int = Field(0, ge=0)
    num_demands_unsatisfied:        int = Field(0, ge=0)
    objective_value:     float = Field(0.0)
    solver_wall_time_ms: float = Field(0.0, ge=0)
    message: str = ""

