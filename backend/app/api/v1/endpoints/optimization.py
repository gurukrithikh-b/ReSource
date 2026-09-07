"""
Optimization API Endpoints — Phase 4, Step 2: Optimization API Integration
========================================================================
Exposes the multi-point OR-Tools allocation solver through FastAPI endpoints.

Endpoints:
  POST /optimization/run     — Execute full multi-point allocation solver pipeline
  GET  /optimization/summary — Summary metrics of the latest allocation optimization
"""

from datetime import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.surplus import SurplusListing, SurplusStatus
from app.models.demand import DemandListing, DemandStatus
from app.models.organization import Organization
from app.api.v1.endpoints.matching import _run_match, _org_coords
from app.optimization.allocation_solver import (
    allocation_solver,
    SolverInput,
    SurplusInput,
    DemandInput,
    ViableMatch,
    SolverOutput,
)
from app.schemas.optimization import (
    OptimizationResultSchema,
    AllocationOutputSchema,
    OptimizationSummarySchema,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _get_org_name(db: Session, org_id: Optional[str]) -> Optional[str]:
    """Retrieve organization name by ID, returning None if missing."""
    if not org_id:
        return None
    org = db.query(Organization).filter(Organization.id == org_id).first()
    return org.name if org else None


def _build_solver_input(db: Session) -> tuple[SolverInput, Dict[str, SurplusListing], Dict[str, DemandListing]]:
    """
    Fetch eligible surplus and demand listings from DB, evaluate Phase 3.3 viability,
    and construct the SolverInput for the OR-Tools optimizer.
    """
    now = datetime.utcnow()

    # 1. Fetch available surplus
    surpluses = db.query(SurplusListing).filter(
        SurplusListing.status.in_([SurplusStatus.AVAILABLE, SurplusStatus.MATCHED])
    ).all()

    valid_surpluses: List[SurplusListing] = []
    for s in surpluses:
        if s.remaining_quantity <= 0:
            continue
        if s.expires_at:
            exp = s.expires_at.replace(tzinfo=None) if s.expires_at.tzinfo else s.expires_at
            if exp <= now:
                continue
        valid_surpluses.append(s)

    # 2. Fetch open demands
    demands = db.query(DemandListing).filter(
        DemandListing.status.in_([DemandStatus.OPEN, DemandStatus.PARTIALLY_MATCHED])
    ).all()

    valid_demands: List[DemandListing] = []
    for d in demands:
        needed = d.requested_quantity - (d.fulfilled_quantity or 0.0)
        if needed > 0:
            valid_demands.append(d)

    # 3. Build SurplusInput items
    surplus_inputs: List[SurplusInput] = []
    for s in valid_surpluses:
        lat, lon = _org_coords(db, s.supplier_id)
        cat_name = s.category.name if s.category else ""
        surplus_inputs.append(SurplusInput(
            id=s.id,
            remaining_quantity=s.remaining_quantity,
            expires_at=s.expires_at,
            storage_condition=s.storage_condition.value if s.storage_condition else "AMBIENT",
            supplier_lat=lat,
            supplier_lon=lon,
            category_id=s.category_id,
            category_name=cat_name,
            title=s.title,
        ))

    # 4. Build DemandInput items
    demand_inputs: List[DemandInput] = []
    for d in valid_demands:
        lat, lon = _org_coords(db, d.receiver_id)
        cat_name = d.category.name if d.category else ""
        demand_inputs.append(DemandInput(
            id=d.id,
            requested_quantity=d.requested_quantity,
            fulfilled_quantity=d.fulfilled_quantity or 0.0,
            required_by=d.required_by,
            urgency_level=d.urgency_level.value if d.urgency_level else "MEDIUM",
            storage_capacity=d.storage_capacity if d.storage_capacity else "AMBIENT",
            receiver_lat=lat,
            receiver_lon=lon,
            category_id=d.category_id,
            category_name=cat_name,
            title=d.title,
        ))

    # 5. Run Phase 3.3 viability matching across all (surplus, demand) pairs
    viable_matches: List[ViableMatch] = []
    for s in valid_surpluses:
        for d in valid_demands:
            match_res = _run_match(s, d, db)
            if match_res.is_viable:
                viable_matches.append(ViableMatch(
                    surplus_id=s.id,
                    demand_id=d.id,
                    match_score=match_res.overall_score,
                    distance_km=match_res.distance_km,
                ))

    solver_input = SolverInput(
        surplus_items=surplus_inputs,
        demand_items=demand_inputs,
        viable_matches=viable_matches,
    )

    surplus_map = {s.id: s for s in valid_surpluses}
    demand_map  = {d.id: d for d in valid_demands}

    return solver_input, surplus_map, demand_map


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    response_model=OptimizationResultSchema,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-point resource allocation optimization",
    description=(
        "Queries active surplus and open demand listings, pre-screens pairs using Phase 3.3 "
        "matching viability, and solves the global allocation Linear Program using Google OR-Tools. "
        "Returns optimal allocations enriched with display metadata."
    ),
)
def run_optimization(db: Session = Depends(get_db)) -> OptimizationResultSchema:
    """Run global OR-Tools allocation optimization for all active surplus and demand."""
    solver_input, surplus_map, demand_map = _build_solver_input(db)

    output: SolverOutput = allocation_solver.solve(solver_input)

    # Enrich allocations with display titles & org names
    enriched_allocations: List[AllocationOutputSchema] = []
    for alloc in output.allocations:
        surplus_obj = surplus_map.get(alloc.surplus_id)
        demand_obj  = demand_map.get(alloc.demand_id)

        supplier_name = _get_org_name(db, surplus_obj.supplier_id) if surplus_obj else None
        receiver_name = _get_org_name(db, demand_obj.receiver_id) if demand_obj else None
        sup_lat, sup_lon = _org_coords(db, surplus_obj.supplier_id) if surplus_obj else (None, None)
        rec_lat, rec_lon = _org_coords(db, demand_obj.receiver_id) if demand_obj else (None, None)

        cat_name = None
        if surplus_obj and surplus_obj.category:
            cat_name = surplus_obj.category.name
        elif demand_obj and demand_obj.category:
            cat_name = demand_obj.category.name

        enriched_allocations.append(AllocationOutputSchema(
            surplus_id=alloc.surplus_id,
            demand_id=alloc.demand_id,
            allocated_quantity=alloc.allocated_quantity,
            match_score=alloc.match_score,
            distance_km=alloc.distance_km,
            status=alloc.status,
            surplus_title=surplus_obj.title if surplus_obj else None,
            surplus_unit=surplus_obj.unit if surplus_obj else None,
            supplier_name=supplier_name,
            supplier_lat=sup_lat,
            supplier_lon=sup_lon,
            demand_title=demand_obj.title if demand_obj else None,
            demand_unit=demand_obj.unit if demand_obj else None,
            receiver_name=receiver_name,
            receiver_lat=rec_lat,
            receiver_lon=rec_lon,
            category_name=cat_name,
        ))

    # Auto-log impact records for generated allocations (Phase 5 integration)
    if enriched_allocations:
        from app.impact.impact_calculator import impact_calculator
        impact_items = []
        for alloc in enriched_allocations:
            surplus_obj = surplus_map.get(alloc.surplus_id)
            demand_obj  = demand_map.get(alloc.demand_id)
            impact_items.append({
                "allocation_id": f"{alloc.surplus_id}_{alloc.demand_id}",
                "allocated_quantity": alloc.allocated_quantity,
                "category_name": alloc.category_name,
                "supplier_id": surplus_obj.supplier_id if surplus_obj else None,
                "supplier_name": alloc.supplier_name,
                "receiver_id": demand_obj.receiver_id if demand_obj else None,
                "receiver_name": alloc.receiver_name,
            })
        impact_calculator.process_batch_allocations(db, impact_items)


    return OptimizationResultSchema(
        status=output.status,
        total_supply_available=output.total_supply_available,
        total_demand_requested=output.total_demand_requested,
        total_allocated=output.total_allocated,
        total_unallocated=output.total_unallocated,
        total_unmet_demand=output.total_unmet_demand,
        num_allocations=output.num_allocations,
        num_demands_fully_satisfied=output.num_demands_fully_satisfied,
        num_demands_partially_satisfied=output.num_demands_partially_satisfied,
        num_demands_unsatisfied=output.num_demands_unsatisfied,
        objective_value=output.objective_value,
        solver_wall_time_ms=output.solver_wall_time_ms,
        allocations=enriched_allocations,
        message=output.message,
    )


@router.get(
    "/summary",
    response_model=OptimizationSummarySchema,
    status_code=status.HTTP_200_OK,
    summary="Get optimization summary statistics",
    description=(
        "Computes allocation optimization metrics for current supply/demand without "
        "returning full allocation detail lists. Ideal for dashboard widgets."
    ),
)
def get_optimization_summary(db: Session = Depends(get_db)) -> OptimizationSummarySchema:
    """Return summary allocation statistics for current supply and demand."""
    solver_input, _, _ = _build_solver_input(db)
    output: SolverOutput = allocation_solver.solve(solver_input)

    return OptimizationSummarySchema(
        status=output.status,
        total_supply_available=output.total_supply_available,
        total_demand_requested=output.total_demand_requested,
        total_allocated=output.total_allocated,
        total_unallocated=output.total_unallocated,
        total_unmet_demand=output.total_unmet_demand,
        num_allocations=output.num_allocations,
        num_demands_fully_satisfied=output.num_demands_fully_satisfied,
        num_demands_partially_satisfied=output.num_demands_partially_satisfied,
        num_demands_unsatisfied=output.num_demands_unsatisfied,
        objective_value=output.objective_value,
        solver_wall_time_ms=output.solver_wall_time_ms,
        message=output.message,
    )
