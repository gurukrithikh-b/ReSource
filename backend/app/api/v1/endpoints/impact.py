"""
Phase 5 — Sustainability Impact Intelligence API Endpoints
==========================================================
Provides REST endpoints for impact calculation, metrics aggregation,
trends analysis, category grouping, provider contribution, and community reach.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.impact import ImpactLog
from app.impact.impact_calculator import impact_calculator
from app.api.v1.endpoints.optimization import _build_solver_input, _get_org_name, _org_coords
from app.optimization.allocation_solver import allocation_solver, SolverOutput
from app.schemas.impact import (
    ImpactCalculateRequest,
    ImpactRecordSchema,
    ImpactSummarySchema,
    ImpactTrendItemSchema,
    ImpactCategoryGroupSchema,
    ImpactProviderGroupSchema,
    ImpactPartnerGroupSchema,
)

router = APIRouter()


def _ensure_impact_populated(db: Session) -> List[ImpactLog]:
    """
    Helper: Ensures that ImpactLog table has entries generated from current solver allocations if empty.
    """
    logs = db.query(ImpactLog).all()
    if logs:
        return logs

    # Automatically generate impact logs from latest solver allocations if table is empty
    solver_input, surplus_map, demand_map = _build_solver_input(db)
    output: SolverOutput = allocation_solver.solve(solver_input)

    batch_items = []
    for alloc in output.allocations:
        surplus_obj = surplus_map.get(alloc.surplus_id)
        demand_obj = demand_map.get(alloc.demand_id)

        sup_name = _get_org_name(db, surplus_obj.supplier_id) if surplus_obj else "Resource Provider"
        rec_name = _get_org_name(db, demand_obj.receiver_id) if demand_obj else "Community Partner"

        cat_name = "Food Surplus"
        if surplus_obj and surplus_obj.category:
            cat_name = surplus_obj.category.name
        elif demand_obj and demand_obj.category:
            cat_name = demand_obj.category.name

        alloc_id = f"{alloc.surplus_id}_{alloc.demand_id}"

        class BatchItem:
            pass

        item = BatchItem()
        item.id = alloc_id
        item.surplus_id = alloc.surplus_id
        item.demand_id = alloc.demand_id
        item.allocated_quantity = alloc.allocated_quantity
        item.category_name = cat_name
        item.supplier_id = surplus_obj.supplier_id if surplus_obj else None
        item.supplier_name = sup_name
        item.receiver_id = demand_obj.receiver_id if demand_obj else None
        item.receiver_name = rec_name
        batch_items.append(item)

    if batch_items:
        return impact_calculator.process_batch_allocations(db, batch_items)
    return []


@router.post(
    "/calculate",
    response_model=List[ImpactRecordSchema],
    status_code=status.HTTP_200_OK,
    summary="Calculate and store impact for allocations",
    description="Calculates impact metrics for provided allocation payloads and stores them idempotently.",
)
def calculate_and_store_impact(
    payload: ImpactCalculateRequest,
    db: Session = Depends(get_db)
) -> List[ImpactRecordSchema]:
    """Calculate and store impact for allocated items."""
    logs = impact_calculator.process_batch_allocations(db, payload.allocations)
    return logs


@router.get(
    "/summary",
    response_model=ImpactSummarySchema,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated sustainability impact metrics",
    description="Returns high-level aggregated sustainability impact totals from successful allocations.",
)
def get_impact_summary(db: Session = Depends(get_db)) -> ImpactSummarySchema:
    """Return aggregated summary metrics."""
    logs = _ensure_impact_populated(db)

    if not logs:
        return ImpactSummarySchema(
            total_resources_rescued_kg=0.0,
            total_demand_fulfilled_kg=0.0,
            total_meals_served=0.0,
            total_co2_avoided_kg=0.0,
            unique_community_partners=0,
            total_successful_allocations=0,
            message="No impact data available yet.",
        )

    total_rescued = sum(log.resource_recovered_kg or 0.0 for log in logs)
    total_fulfilled = sum(log.demand_fulfilled_kg or log.resource_recovered_kg or 0.0 for log in logs)
    total_meals = sum(log.meals_provided_estimate or 0.0 for log in logs)
    total_co2 = sum(log.co2_avoided_kg or 0.0 for log in logs)

    unique_partners = len(set(
        log.receiver_name for log in logs if log.receiver_name
    ))

    return ImpactSummarySchema(
        total_resources_rescued_kg=round(total_rescued, 1),
        total_demand_fulfilled_kg=round(total_fulfilled, 1),
        total_meals_served=round(total_meals, 1),
        total_co2_avoided_kg=round(total_co2, 1),
        unique_community_partners=unique_partners,
        total_successful_allocations=len(logs),
        message="Sustainability impact calculated from optimized allocations",
    )


@router.get(
    "/allocations",
    response_model=List[ImpactRecordSchema],
    status_code=status.HTTP_200_OK,
    summary="Get allocation-level impact details",
    description="Returns allocation-level impact log records.",
)
def get_allocation_impacts(db: Session = Depends(get_db)) -> List[ImpactRecordSchema]:
    """Return all allocation-level impact records."""
    logs = _ensure_impact_populated(db)
    return logs


@router.get(
    "/trends",
    response_model=List[ImpactTrendItemSchema],
    status_code=status.HTTP_200_OK,
    summary="Get time-based impact trends",
    description="Returns impact metrics aggregated over time by day, week, or month.",
)
def get_impact_trends(
    group_by: str = Query("day", enum=["day", "week", "month"]),
    db: Session = Depends(get_db)
) -> List[ImpactTrendItemSchema]:
    """Return time-series aggregated impact data for analytics charts."""
    logs = _ensure_impact_populated(db)

    if not logs:
        return []

    # Group by formatted date
    grouped: dict = {}
    for log in logs:
        dt = log.calculated_at or datetime.utcnow()
        if group_by == "month":
            date_key = dt.strftime("%Y-%m")
        elif group_by == "week":
            date_key = dt.strftime("%Y-W%U")
        else:
            date_key = dt.strftime("%Y-%m-%d")

        if date_key not in grouped:
            grouped[date_key] = {
                "date": date_key,
                "resources_rescued_kg": 0.0,
                "demand_fulfilled_kg": 0.0,
                "co2_avoided_kg": 0.0,
                "meals_served": 0.0,
                "allocations_count": 0,
            }

        grouped[date_key]["resources_rescued_kg"] += log.resource_recovered_kg or 0.0
        grouped[date_key]["demand_fulfilled_kg"] += log.demand_fulfilled_kg or log.resource_recovered_kg or 0.0
        grouped[date_key]["co2_avoided_kg"] += log.co2_avoided_kg or 0.0
        grouped[date_key]["meals_served"] += log.meals_provided_estimate or 0.0
        grouped[date_key]["allocations_count"] += 1

    trend_items = []
    for k in sorted(grouped.keys()):
        item = grouped[k]
        trend_items.append(ImpactTrendItemSchema(
            date=item["date"],
            resources_rescued_kg=round(item["resources_rescued_kg"], 1),
            demand_fulfilled_kg=round(item["demand_fulfilled_kg"], 1),
            co2_avoided_kg=round(item["co2_avoided_kg"], 1),
            meals_served=round(item["meals_served"], 1),
            allocations_count=item["allocations_count"],
        ))

    return trend_items


@router.get(
    "/categories",
    response_model=List[ImpactCategoryGroupSchema],
    status_code=status.HTTP_200_OK,
    summary="Get impact grouped by resource category",
    description="Returns impact metrics aggregated by resource category.",
)
def get_impact_by_category(db: Session = Depends(get_db)) -> List[ImpactCategoryGroupSchema]:
    """Return category-level impact breakdown."""
    logs = _ensure_impact_populated(db)

    grouped: dict = {}
    for log in logs:
        cat = log.category or "Food Surplus"
        if cat not in grouped:
            grouped[cat] = {
                "category": cat,
                "resources_rescued_kg": 0.0,
                "co2_avoided_kg": 0.0,
                "meals_served": 0.0,
                "allocations_count": 0,
            }
        grouped[cat]["resources_rescued_kg"] += log.resource_recovered_kg or 0.0
        grouped[cat]["co2_avoided_kg"] += log.co2_avoided_kg or 0.0
        grouped[cat]["meals_served"] += log.meals_provided_estimate or 0.0
        grouped[cat]["allocations_count"] += 1

    res = []
    for cat in sorted(grouped.keys()):
        item = grouped[cat]
        res.append(ImpactCategoryGroupSchema(
            category=item["category"],
            resources_rescued_kg=round(item["resources_rescued_kg"], 1),
            co2_avoided_kg=round(item["co2_avoided_kg"], 1),
            meals_served=round(item["meals_served"], 1),
            allocations_count=item["allocations_count"],
        ))
    return res


@router.get(
    "/providers",
    response_model=List[ImpactProviderGroupSchema],
    status_code=status.HTTP_200_OK,
    summary="Get impact grouped by resource provider",
    description="Returns impact metrics aggregated by resource supplier/provider.",
)
def get_impact_by_provider(db: Session = Depends(get_db)) -> List[ImpactProviderGroupSchema]:
    """Return provider contribution impact breakdown."""
    logs = _ensure_impact_populated(db)

    grouped: dict = {}
    for log in logs:
        provider = log.supplier_name or "Resource Provider"
        if provider not in grouped:
            grouped[provider] = {
                "provider_name": provider,
                "resources_rescued_kg": 0.0,
                "co2_avoided_kg": 0.0,
                "meals_served": 0.0,
                "allocations_count": 0,
            }
        grouped[provider]["resources_rescued_kg"] += log.resource_recovered_kg or 0.0
        grouped[provider]["co2_avoided_kg"] += log.co2_avoided_kg or 0.0
        grouped[provider]["meals_served"] += log.meals_provided_estimate or 0.0
        grouped[provider]["allocations_count"] += 1

    res = []
    for provider in sorted(grouped.keys()):
        item = grouped[provider]
        res.append(ImpactProviderGroupSchema(
            provider_name=item["provider_name"],
            resources_rescued_kg=round(item["resources_rescued_kg"], 1),
            co2_avoided_kg=round(item["co2_avoided_kg"], 1),
            meals_served=round(item["meals_served"], 1),
            allocations_count=item["allocations_count"],
        ))
    return res


@router.get(
    "/partners",
    response_model=List[ImpactPartnerGroupSchema],
    status_code=status.HTTP_200_OK,
    summary="Get impact grouped by community partner",
    description="Returns impact metrics aggregated by community partner receiver.",
)
def get_impact_by_partner(db: Session = Depends(get_db)) -> List[ImpactPartnerGroupSchema]:
    """Return community reach partner impact breakdown."""
    logs = _ensure_impact_populated(db)

    grouped: dict = {}
    for log in logs:
        partner = log.receiver_name or "Community Partner"
        if partner not in grouped:
            grouped[partner] = {
                "partner_name": partner,
                "resources_rescued_kg": 0.0,
                "demand_fulfilled_kg": 0.0,
                "meals_served": 0.0,
                "allocations_count": 0,
            }
        grouped[partner]["resources_rescued_kg"] += log.resource_recovered_kg or 0.0
        grouped[partner]["demand_fulfilled_kg"] += log.demand_fulfilled_kg or log.resource_recovered_kg or 0.0
        grouped[partner]["meals_served"] += log.meals_provided_estimate or 0.0
        grouped[partner]["allocations_count"] += 1

    res = []
    for partner in sorted(grouped.keys()):
        item = grouped[partner]
        res.append(ImpactPartnerGroupSchema(
            partner_name=item["partner_name"],
            resources_rescued_kg=round(item["resources_rescued_kg"], 1),
            demand_fulfilled_kg=round(item["demand_fulfilled_kg"], 1),
            meals_served=round(item["meals_served"], 1),
            allocations_count=item["allocations_count"],
        ))
    return res
