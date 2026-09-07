"""
Phase 4 Step 1 Tests — Core OR-Tools Allocation Solver
=======================================================
All tests use small, deterministic synthetic datasets (no DB, no network).
Tests are fully self-contained.

Coverage:
  1.  One surplus → one demand                        (basic allocation)
  2.  One surplus → multiple demands                  (supply split)
  3.  Multiple surplus → one demand                   (demand filled from multiple)
  4.  Multiple surplus → multiple demands             (global optimum)
  5.  Supply constraint — never over-allocate surplus
  6.  Demand constraint — never over-allocate demand
  7.  Incompatible matches excluded
  8.  Expired surplus excluded (no viable matches)
  9.  Partial allocation when supply < demand
  10. Full allocation when supply ≥ demand
  11. Zero surplus (empty list)
  12. Zero demand  (empty list)
  13. No viable matches
  14. Higher match score preference
  15. Distance preference
  16. Allocation quantities never negative
  17. Total allocation never exceeds supply
  18. Total allocation never exceeds demand
  19. Valid solver status returned
  20. Output summary correctness
  21. SolverOutput schema — all required fields present
  22. Objective value is positive for viable problem
  23. Solver handles equal supply and demand exactly
  24. Multiple demands unsatisfied when supply insufficient
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.optimization.allocation_solver import (
    AllocationSolver,
    SolverInput,
    SurplusInput,
    DemandInput,
    ViableMatch,
    SolverStatus,
    AllocationStatus,
    MIN_ALLOC_KG,
)

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

NOW     = datetime(2025, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
FUTURE  = NOW + timedelta(hours=12)   # surplus valid for 12 hours
EXPIRED = NOW - timedelta(hours=1)    # already expired

@pytest.fixture(scope="module")
def solver():
    return AllocationSolver()


def make_surplus(sid, qty, storage="AMBIENT", lat=12.97, lon=77.59,
                 cat_id="cat-food", expires=None):
    return SurplusInput(
        id=sid,
        remaining_quantity=qty,
        expires_at=expires or FUTURE,
        storage_condition=storage,
        supplier_lat=lat,
        supplier_lon=lon,
        category_id=cat_id,
        category_name="Food",
        title=f"Surplus {sid}",
    )


def make_demand(did, qty, urgency="MEDIUM", storage="AMBIENT", lat=12.96, lon=77.60,
                cat_id="cat-food", fulfilled=0.0):
    return DemandInput(
        id=did,
        requested_quantity=qty,
        fulfilled_quantity=fulfilled,
        required_by=FUTURE,
        urgency_level=urgency,
        storage_capacity=storage,
        receiver_lat=lat,
        receiver_lon=lon,
        category_id=cat_id,
        category_name="Food",
        title=f"Demand {did}",
    )


def make_match(sid, did, score=80.0, dist=3.0):
    return ViableMatch(surplus_id=sid, demand_id=did, match_score=score, distance_km=dist)


# ===========================================================================
# 1. One surplus → one demand
# ===========================================================================

class TestOneToOne:
    def test_basic_allocation_succeeds(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(out.allocations) == 1
        assert out.allocations[0].surplus_id == "s1"
        assert out.allocations[0].demand_id  == "d1"

    def test_allocation_satisfies_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(80.0, abs=0.01)
        assert out.num_demands_fully_satisfied == 1

    def test_allocation_does_not_exceed_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 500.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated <= 80.0 + 0.01

    def test_allocation_does_not_exceed_supply(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 50.0)],
            demand_items=[make_demand("d1", 200.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated <= 50.0 + 0.01


# ===========================================================================
# 2. One surplus → multiple demands
# ===========================================================================

class TestOneToMany:
    def test_surplus_split_across_demands(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 60.0), make_demand("d2", 60.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s1", "d2")],
        )
        out = solver.solve(inp)
        assert out.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert out.total_allocated == pytest.approx(100.0, abs=0.01)

    def test_supply_constraint_respected_one_to_many(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0), make_demand("d2", 80.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s1", "d2")],
        )
        out = solver.solve(inp)
        total = sum(a.allocated_quantity for a in out.allocations)
        assert total <= 100.0 + 0.01  # never exceeds surplus

    def test_higher_score_demand_gets_more_when_constrained(self, solver):
        """When supply is limited, higher-score demand should receive priority."""
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 60.0)],
            demand_items=[make_demand("d1", 60.0), make_demand("d2", 60.0)],
            viable_matches=[
                make_match("s1", "d1", score=95.0),  # high score
                make_match("s1", "d2", score=30.0),  # low score
            ],
        )
        out = solver.solve(inp)
        d1_alloc = next((a.allocated_quantity for a in out.allocations if a.demand_id == "d1"), 0.0)
        d2_alloc = next((a.allocated_quantity for a in out.allocations if a.demand_id == "d2"), 0.0)
        assert d1_alloc >= d2_alloc  # high-score demand prioritised


# ===========================================================================
# 3. Multiple surplus → one demand
# ===========================================================================

class TestManyToOne:
    def test_multiple_suppliers_fill_one_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 30.0), make_surplus("s2", 40.0)],
            demand_items=[make_demand("d1", 60.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s2", "d1")],
        )
        out = solver.solve(inp)
        assert out.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert out.total_allocated == pytest.approx(60.0, abs=0.01)
        assert out.num_demands_fully_satisfied == 1

    def test_demand_constraint_many_to_one(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 200.0), make_surplus("s2", 200.0)],
            demand_items=[make_demand("d1", 50.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s2", "d1")],
        )
        out = solver.solve(inp)
        total = sum(a.allocated_quantity for a in out.allocations)
        assert total <= 50.0 + 0.01  # never over-fills demand


# ===========================================================================
# 4. Multiple surplus → multiple demands (global optimum)
# ===========================================================================

class TestManyToMany:
    def test_global_allocation_example(self, solver):
        """
        Hotel:500, Restaurant:300, EventCenter:200
        NGO A:400, NGO B:350, Shelter C:250  (total demand=1000, total supply=1000)
        """
        inp = SolverInput(
            surplus_items=[
                make_surplus("hotel",    500.0),
                make_surplus("rest",     300.0),
                make_surplus("event",    200.0),
            ],
            demand_items=[
                make_demand("ngo_a",    400.0),
                make_demand("ngo_b",    350.0),
                make_demand("shelter",  250.0),
            ],
            viable_matches=[
                make_match("hotel",  "ngo_a",   score=90.0, dist=2.0),
                make_match("hotel",  "ngo_b",   score=85.0, dist=4.0),
                make_match("hotel",  "shelter", score=80.0, dist=6.0),
                make_match("rest",   "ngo_a",   score=75.0, dist=3.0),
                make_match("rest",   "ngo_b",   score=82.0, dist=2.5),
                make_match("rest",   "shelter", score=78.0, dist=5.0),
                make_match("event",  "ngo_b",   score=70.0, dist=7.0),
                make_match("event",  "shelter", score=88.0, dist=1.5),
            ],
        )
        out = solver.solve(inp)
        assert out.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert out.total_allocated == pytest.approx(1000.0, abs=0.1)
        assert out.total_unallocated < 0.1
        assert out.total_unmet_demand < 0.1

    def test_many_to_many_supply_constraints(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0), make_surplus("s2", 150.0)],
            demand_items=[make_demand("d1", 200.0), make_demand("d2", 200.0)],
            viable_matches=[
                make_match("s1", "d1"), make_match("s1", "d2"),
                make_match("s2", "d1"), make_match("s2", "d2"),
            ],
        )
        out = solver.solve(inp)
        # total supply = 250, total demand = 400 → allocate all supply
        assert out.total_allocated == pytest.approx(250.0, abs=0.01)

    def test_many_to_many_demand_constraints(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 300.0), make_surplus("s2", 300.0)],
            demand_items=[make_demand("d1", 50.0), make_demand("d2", 50.0)],
            viable_matches=[
                make_match("s1", "d1"), make_match("s1", "d2"),
                make_match("s2", "d1"), make_match("s2", "d2"),
            ],
        )
        out = solver.solve(inp)
        # total demand = 100, so allocate at most 100
        assert out.total_allocated == pytest.approx(100.0, abs=0.01)


# ===========================================================================
# 5 & 6. Supply and demand constraint correctness
# ===========================================================================

class TestConstraints:
    def test_allocation_never_exceeds_any_single_surplus(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 30.0), make_surplus("s2", 20.0)],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s2", "d1")],
        )
        out = solver.solve(inp)
        s1_total = sum(a.allocated_quantity for a in out.allocations if a.surplus_id == "s1")
        s2_total = sum(a.allocated_quantity for a in out.allocations if a.surplus_id == "s2")
        assert s1_total <= 30.0 + 0.01
        assert s2_total <= 20.0 + 0.01

    def test_allocation_never_exceeds_any_single_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 500.0)],
            demand_items=[make_demand("d1", 40.0), make_demand("d2", 30.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s1", "d2")],
        )
        out = solver.solve(inp)
        d1_total = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d1")
        d2_total = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d2")
        assert d1_total <= 40.0 + 0.01
        assert d2_total <= 30.0 + 0.01

    def test_no_allocation_quantity_is_negative(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0), make_surplus("s2", 50.0)],
            demand_items=[make_demand("d1", 80.0), make_demand("d2", 60.0)],
            viable_matches=[
                make_match("s1", "d1"), make_match("s1", "d2"),
                make_match("s2", "d1"), make_match("s2", "d2"),
            ],
        )
        out = solver.solve(inp)
        for alloc in out.allocations:
            assert alloc.allocated_quantity >= 0.0


# ===========================================================================
# 7. Incompatible matches excluded
# ===========================================================================

class TestIncompatibleExcluded:
    def test_incompatible_pair_not_in_viable_list_means_no_allocation(self, solver):
        """
        Incompatible pairs are excluded by not appearing in viable_matches.
        The solver must produce zero allocation (NO_DATA) with an empty viable list.
        """
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[],  # no viable pairs
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0
        assert len(out.allocations) == 0

    def test_only_viable_pairs_receive_allocation(self, solver):
        """
        s1→d2 is not in viable_matches; it should not appear in allocations.
        """
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 50.0), make_demand("d2", 50.0)],
            viable_matches=[make_match("s1", "d1")],  # only d1 is viable
        )
        out = solver.solve(inp)
        demand_ids = {a.demand_id for a in out.allocations}
        assert "d2" not in demand_ids


# ===========================================================================
# 8. Expired surplus excluded
# ===========================================================================

class TestExpiredSurplus:
    def test_expired_surplus_yields_no_data(self, solver):
        """Expired surplus is pre-screened out by Phase 3.3 — no viable matches."""
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0, expires=EXPIRED)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[],   # Phase 3.3 would have screened this out
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0

    def test_mix_expired_and_valid_surplus(self, solver):
        """Only the non-expired surplus contributes to allocation."""
        inp = SolverInput(
            surplus_items=[
                make_surplus("s_exp",   200.0, expires=EXPIRED),   # expired — screened by Phase 3.3
                make_surplus("s_valid", 100.0),                     # valid
            ],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s_valid", "d1")],  # only valid surplus is viable
        )
        out = solver.solve(inp)
        assert out.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        # Only the valid surplus should appear in allocations
        surplus_ids = {a.surplus_id for a in out.allocations}
        assert "s_exp" not in surplus_ids
        assert "s_valid" in surplus_ids


# ===========================================================================
# 9 & 10. Partial and full allocation
# ===========================================================================

class TestPartialAndFullAllocation:
    def test_partial_allocation_when_supply_less_than_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 40.0)],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(40.0, abs=0.01)
        assert out.total_unmet_demand == pytest.approx(60.0, abs=0.01)
        assert out.num_demands_partially_satisfied == 1
        assert out.num_demands_fully_satisfied == 0

    def test_full_allocation_when_supply_equals_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(100.0, abs=0.01)
        assert out.num_demands_fully_satisfied == 1
        assert out.total_unmet_demand < 0.01

    def test_full_allocation_when_supply_exceeds_demand(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 300.0)],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(100.0, abs=0.01)
        assert out.total_unallocated == pytest.approx(200.0, abs=0.01)


# ===========================================================================
# 11 & 12. Empty input edge cases
# ===========================================================================

class TestEmptyInputs:
    def test_no_surplus_returns_no_data(self, solver):
        inp = SolverInput(
            surplus_items=[],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0

    def test_no_demand_returns_no_data(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[],
            viable_matches=[],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0

    def test_zero_remaining_surplus_returns_no_data(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 0.0)],
            demand_items=[make_demand("d1", 100.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0

    def test_fully_fulfilled_demand_returns_no_data(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 100.0, fulfilled=100.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0


# ===========================================================================
# 13. No viable matches
# ===========================================================================

class TestNoViableMatches:
    def test_no_viable_matches_no_data(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA
        assert out.total_allocated == 0.0
        assert len(out.allocations) == 0

    def test_message_is_informative(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[],
        )
        out = solver.solve(inp)
        assert len(out.message) > 0


# ===========================================================================
# 14 & 15. Match score and distance preference
# ===========================================================================

class TestObjectivePreferences:
    def test_higher_match_score_preferred_when_supply_constrained(self, solver):
        """
        s1 (100 kg) can go to d1 (score 95) or d2 (score 40), but only has 100 kg.
        Both demands need 100 kg → solver should prioritise d1 (higher score).
        """
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 100.0), make_demand("d2", 100.0)],
            viable_matches=[
                make_match("s1", "d1", score=95.0, dist=2.0),
                make_match("s1", "d2", score=40.0, dist=2.0),
            ],
        )
        out = solver.solve(inp)
        d1_qty = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d1")
        d2_qty = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d2")
        assert d1_qty >= d2_qty

    def test_closer_distance_preferred_when_scores_equal(self, solver):
        """
        Same score, different distances → nearer demand should get more allocation.
        """
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 80.0)],
            demand_items=[make_demand("d1", 80.0), make_demand("d2", 80.0)],
            viable_matches=[
                make_match("s1", "d1", score=80.0, dist=2.0),   # near
                make_match("s1", "d2", score=80.0, dist=45.0),  # far
            ],
        )
        out = solver.solve(inp)
        d1_qty = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d1")
        d2_qty = sum(a.allocated_quantity for a in out.allocations if a.demand_id == "d2")
        assert d1_qty >= d2_qty


# ===========================================================================
# 16–18. Invariant property tests
# ===========================================================================

class TestInvariants:
    def _varied_scenarios(self):
        return [
            SolverInput(
                surplus_items=[make_surplus("s1", 100.0)],
                demand_items=[make_demand("d1", 80.0)],
                viable_matches=[make_match("s1", "d1")],
            ),
            SolverInput(
                surplus_items=[make_surplus("s1", 200.0), make_surplus("s2", 150.0)],
                demand_items=[make_demand("d1", 100.0), make_demand("d2", 120.0)],
                viable_matches=[
                    make_match("s1", "d1"), make_match("s1", "d2"),
                    make_match("s2", "d1"), make_match("s2", "d2"),
                ],
            ),
            SolverInput(
                surplus_items=[make_surplus("s1", 50.0)],
                demand_items=[make_demand("d1", 300.0)],
                viable_matches=[make_match("s1", "d1")],
            ),
        ]

    def test_allocation_quantities_never_negative(self, solver):
        for inp in self._varied_scenarios():
            out = solver.solve(inp)
            for alloc in out.allocations:
                assert alloc.allocated_quantity >= 0.0

    def test_total_allocation_never_exceeds_total_supply(self, solver):
        for inp in self._varied_scenarios():
            out = solver.solve(inp)
            total_sup = sum(s.remaining_quantity for s in inp.surplus_items)
            assert out.total_allocated <= total_sup + 0.01

    def test_total_allocation_never_exceeds_total_demand(self, solver):
        for inp in self._varied_scenarios():
            out = solver.solve(inp)
            total_dem = sum(d.needed_quantity for d in inp.demand_items)
            assert out.total_allocated <= total_dem + 0.01


# ===========================================================================
# 19. Valid solver status
# ===========================================================================

class TestSolverStatus:
    def test_optimal_status_for_feasible_problem(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.status == SolverStatus.OPTIMAL

    def test_no_data_status_for_empty_surplus(self, solver):
        inp = SolverInput(surplus_items=[], demand_items=[make_demand("d1", 80.0)])
        out = solver.solve(inp)
        assert out.status == SolverStatus.NO_DATA

    def test_status_is_always_a_valid_enum_value(self, solver):
        for inp in [
            SolverInput(surplus_items=[], demand_items=[]),
            SolverInput(
                surplus_items=[make_surplus("s1", 10.0)],
                demand_items=[make_demand("d1", 10.0)],
                viable_matches=[make_match("s1", "d1")],
            ),
        ]:
            out = solver.solve(inp)
            assert out.status in SolverStatus.__members__.values()


# ===========================================================================
# 20. Output summary correctness
# ===========================================================================

class TestOutputSummary:
    def test_summary_fields_consistent(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 120.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        assert out.total_allocated + out.total_unallocated == pytest.approx(
            out.total_supply_available, abs=0.01
        )
        assert out.total_unmet_demand == pytest.approx(
            out.total_demand_requested - out.total_allocated, abs=0.01
        )

    def test_demand_satisfaction_counts_sum_to_total_demands(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 50.0)],
            demand_items=[make_demand("d1", 80.0), make_demand("d2", 80.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s1", "d2")],
        )
        out = solver.solve(inp)
        total_demands = len([d for d in inp.demand_items if d.needed_quantity > 0])
        count_sum = (out.num_demands_fully_satisfied
                     + out.num_demands_partially_satisfied
                     + out.num_demands_unsatisfied)
        assert count_sum == total_demands

    def test_num_allocations_matches_allocations_list(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 60.0), make_demand("d2", 30.0)],
            viable_matches=[make_match("s1", "d1"), make_match("s1", "d2")],
        )
        out = solver.solve(inp)
        assert out.num_allocations == len(out.allocations)


# ===========================================================================
# 21. Schema — all required fields present
# ===========================================================================

class TestOutputSchema:
    def test_all_required_fields_present_on_output(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        # Ensure all documented fields exist on SolverOutput
        for attr in [
            "status", "total_supply_available", "total_demand_requested",
            "total_allocated", "total_unallocated", "total_unmet_demand",
            "num_allocations", "num_demands_fully_satisfied",
            "num_demands_partially_satisfied", "num_demands_unsatisfied",
            "objective_value", "solver_wall_time_ms", "allocations", "message",
        ]:
            assert hasattr(out, attr), f"Missing field: {attr}"

    def test_allocation_output_fields_present(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1")],
        )
        out = solver.solve(inp)
        for alloc in out.allocations:
            for attr in ["surplus_id", "demand_id", "allocated_quantity",
                         "match_score", "distance_km", "status"]:
                assert hasattr(alloc, attr), f"Missing field on AllocationOutput: {attr}"


# ===========================================================================
# 22. Objective value is positive for a viable problem
# ===========================================================================

class TestObjectiveValue:
    def test_objective_value_positive_for_viable_problem(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 100.0)],
            demand_items=[make_demand("d1", 80.0)],
            viable_matches=[make_match("s1", "d1", score=80.0, dist=3.0)],
        )
        out = solver.solve(inp)
        assert out.objective_value > 0.0

    def test_objective_value_zero_for_no_data(self, solver):
        inp = SolverInput(surplus_items=[], demand_items=[])
        out = solver.solve(inp)
        assert out.objective_value == 0.0


# ===========================================================================
# 23. Exact supply = demand
# ===========================================================================

class TestExactBalance:
    def test_exact_balance_fully_allocated(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 150.0), make_surplus("s2", 100.0)],
            demand_items=[make_demand("d1", 150.0), make_demand("d2", 100.0)],
            viable_matches=[
                make_match("s1", "d1"), make_match("s1", "d2"),
                make_match("s2", "d1"), make_match("s2", "d2"),
            ],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(250.0, abs=0.01)
        assert out.total_unallocated < 0.01
        assert out.total_unmet_demand < 0.01


# ===========================================================================
# 24. Insufficient supply → multiple demands unsatisfied
# ===========================================================================

class TestInsufficientSupply:
    def test_many_demands_unsatisfied_with_little_supply(self, solver):
        inp = SolverInput(
            surplus_items=[make_surplus("s1", 30.0)],
            demand_items=[
                make_demand("d1", 100.0),
                make_demand("d2", 100.0),
                make_demand("d3", 100.0),
            ],
            viable_matches=[
                make_match("s1", "d1"),
                make_match("s1", "d2"),
                make_match("s1", "d3"),
            ],
        )
        out = solver.solve(inp)
        assert out.total_allocated == pytest.approx(30.0, abs=0.01)
        assert out.total_unmet_demand == pytest.approx(270.0, abs=0.01)
        # At most one demand can be partially/fully satisfied
        assert out.num_demands_partially_satisfied >= 1 or out.num_demands_fully_satisfied >= 1
