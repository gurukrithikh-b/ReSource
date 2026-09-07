"""
Matching API Endpoints — Phase 3.3: Smart Compatibility Matching
================================================================
Provides explainable, ranked surplus ↔ demand compatibility matching.

Endpoints:
  GET /matching/surplus/{surplus_id}            — rank all open demands against one surplus
  GET /matching/demand/{demand_id}              — rank all available surplus against one demand
  GET /matching/surplus/{surplus_id}/top        — top-N matches for a surplus (default 5)
  GET /matching/explain/{surplus_id}/{demand_id} — detailed factor breakdown for one pair
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.surplus import SurplusListing, SurplusStatus
from app.models.demand import DemandListing, DemandStatus
from app.models.organization import Organization
from app.matching.scorer import score_match, MatchResult
from app.schemas.matching import (
    MatchResultResponse,
    RankedMatchesResponse,
    RankedMatchItem,
    FactorScores,
    FactorWeights,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _org_coords(db: Session, org_id: str):
    """Return (lat, lon) for an org, or (None, None) if not found."""
    org: Optional[Organization] = db.query(Organization).filter(
        Organization.id == org_id
    ).first()
    if org is None:
        return None, None
    return org.latitude, org.longitude


def _result_to_response(result: MatchResult) -> MatchResultResponse:
    return MatchResultResponse(
        surplus_id=result.surplus_id,
        demand_id=result.demand_id,
        overall_score=result.overall_score,
        factor_scores=FactorScores(
            category=result.factor_scores["category"],
            quantity=result.factor_scores["quantity"],
            distance=result.factor_scores["distance"],
            time=result.factor_scores["time"],
            urgency=result.factor_scores["urgency"],
            storage=result.factor_scores["storage"],
        ),
        reasons=result.reasons,
        is_viable=result.is_viable,
        disqualification_reasons=result.disqualification_reasons,
        distance_km=result.distance_km,
    )


def _result_to_ranked_item(rank: int, result: MatchResult,
                            surplus: SurplusListing,
                            demand: DemandListing,
                            db: Session) -> RankedMatchItem:
    """Enrich a MatchResult with denormalised display fields for the frontend."""
    supplier_name = None
    if surplus.supplier_id:
        org = db.query(Organization).filter(Organization.id == surplus.supplier_id).first()
        supplier_name = org.name if org else None

    receiver_name = None
    if demand.receiver_id:
        org = db.query(Organization).filter(Organization.id == demand.receiver_id).first()
        receiver_name = org.name if org else None

    return RankedMatchItem(
        rank=rank,
        surplus_id=result.surplus_id,
        demand_id=result.demand_id,
        overall_score=result.overall_score,
        factor_scores=FactorScores(
            category=result.factor_scores["category"],
            quantity=result.factor_scores["quantity"],
            distance=result.factor_scores["distance"],
            time=result.factor_scores["time"],
            urgency=result.factor_scores["urgency"],
            storage=result.factor_scores["storage"],
        ),
        reasons=result.reasons,
        is_viable=result.is_viable,
        disqualification_reasons=result.disqualification_reasons,
        distance_km=result.distance_km,
        surplus_title=surplus.title,
        surplus_quantity=surplus.quantity,
        surplus_unit=surplus.unit,
        surplus_storage=surplus.storage_condition.value if surplus.storage_condition else None,
        surplus_expires_at=surplus.expires_at.isoformat() if surplus.expires_at else None,
        demand_title=demand.title,
        demand_requested_quantity=demand.requested_quantity,
        demand_unit=demand.unit,
        demand_urgency=demand.urgency_level.value if demand.urgency_level else None,
        demand_required_by=demand.required_by.isoformat() if demand.required_by else None,
        demand_status=demand.status.value if demand.status else None,
        receiver_name=receiver_name,
        supplier_name=supplier_name,
    )


def _run_match(surplus: SurplusListing, demand: DemandListing, db: Session) -> MatchResult:
    """Run the scorer for one (surplus, demand) pair using DB-resolved coordinates."""
    sup_lat, sup_lon = _org_coords(db, surplus.supplier_id)
    rec_lat, rec_lon = _org_coords(db, demand.receiver_id)

    # Category names — resolve from loaded relationships if available, else empty
    surplus_cat_name = ""
    demand_cat_name  = ""
    if surplus.category:
        surplus_cat_name = surplus.category.name
    if demand.category:
        demand_cat_name = demand.category.name

    return score_match(
        surplus_id=surplus.id,
        surplus_cat_id=surplus.category_id,
        surplus_cat_name=surplus_cat_name,
        surplus_remaining_qty=surplus.remaining_quantity,
        surplus_storage=surplus.storage_condition.value if surplus.storage_condition else "AMBIENT",
        surplus_expires_at=surplus.expires_at,
        supplier_lat=sup_lat,
        supplier_lon=sup_lon,
        demand_id=demand.id,
        demand_cat_id=demand.category_id,
        demand_cat_name=demand_cat_name,
        demand_requested_qty=demand.requested_quantity,
        demand_fulfilled_qty=demand.fulfilled_quantity,
        demand_storage_capacity=demand.storage_capacity,
        demand_urgency=demand.urgency_level.value if demand.urgency_level else "MEDIUM",
        demand_required_by=demand.required_by,
        demand_status=demand.status.value if demand.status else "OPEN",
        receiver_lat=rec_lat,
        receiver_lon=rec_lon,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/surplus/{surplus_id}",
    response_model=RankedMatchesResponse,
    summary="Rank all open demands against a surplus listing",
    description=(
        "Evaluate every open demand listing against the specified surplus and "
        "return them ranked by compatibility score (highest first). "
        "Disqualified matches (expired, fulfilled, incompatible) are appended at the bottom."
    ),
)
def match_surplus_against_demands(
    surplus_id: str,
    include_disqualified: bool = Query(True, description="Include disqualified matches at the bottom"),
    db: Session = Depends(get_db),
) -> RankedMatchesResponse:
    """Match one surplus listing against all open demand listings."""
    surplus = db.query(SurplusListing).filter(SurplusListing.id == surplus_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail=f"Surplus listing '{surplus_id}' not found.")

    # Fetch candidate demands: OPEN or PARTIALLY_MATCHED
    demands = db.query(DemandListing).filter(
        DemandListing.status.in_([DemandStatus.OPEN, DemandStatus.PARTIALLY_MATCHED])
    ).all()

    results: List[MatchResult] = [_run_match(surplus, d, db) for d in demands]

    # Sort: viable first (score desc), then non-viable
    viable   = sorted([r for r in results if r.is_viable],     key=lambda r: -r.overall_score)
    rejected = sorted([r for r in results if not r.is_viable], key=lambda r: -r.overall_score)

    ordered = viable + (rejected if include_disqualified else [])

    demand_map = {d.id: d for d in demands}
    ranked_items = [
        _result_to_ranked_item(i + 1, r, surplus, demand_map[r.demand_id], db)
        for i, r in enumerate(ordered)
    ]

    return RankedMatchesResponse(
        query_type="surplus",
        query_id=surplus_id,
        total_candidates=len(results),
        viable_count=len(viable),
        matches=ranked_items,
    )


@router.get(
    "/demand/{demand_id}",
    response_model=RankedMatchesResponse,
    summary="Rank all available surplus against a demand listing",
    description=(
        "Evaluate every available surplus listing against the specified demand and "
        "return them ranked by compatibility score (highest first)."
    ),
)
def match_demand_against_surplus(
    demand_id: str,
    include_disqualified: bool = Query(True, description="Include disqualified matches at the bottom"),
    db: Session = Depends(get_db),
) -> RankedMatchesResponse:
    """Match one demand listing against all available surplus listings."""
    demand = db.query(DemandListing).filter(DemandListing.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail=f"Demand listing '{demand_id}' not found.")

    # Fetch candidate surplus: AVAILABLE or MATCHED (partially matched)
    surpluses = db.query(SurplusListing).filter(
        SurplusListing.status.in_([SurplusStatus.AVAILABLE, SurplusStatus.MATCHED])
    ).all()

    results: List[MatchResult] = [_run_match(s, demand, db) for s in surpluses]

    viable   = sorted([r for r in results if r.is_viable],     key=lambda r: -r.overall_score)
    rejected = sorted([r for r in results if not r.is_viable], key=lambda r: -r.overall_score)

    ordered = viable + (rejected if include_disqualified else [])

    surplus_map = {s.id: s for s in surpluses}
    ranked_items = [
        _result_to_ranked_item(i + 1, r, surplus_map[r.surplus_id], demand, db)
        for i, r in enumerate(ordered)
    ]

    return RankedMatchesResponse(
        query_type="demand",
        query_id=demand_id,
        total_candidates=len(results),
        viable_count=len(viable),
        matches=ranked_items,
    )


@router.get(
    "/surplus/{surplus_id}/top",
    response_model=List[RankedMatchItem],
    summary="Top-N ranked matches for a surplus listing",
    description="Return only the top N viable matches for a surplus. Useful for dashboard widgets.",
)
def top_matches_for_surplus(
    surplus_id: str,
    limit: int = Query(5, ge=1, le=50, description="Number of top matches to return"),
    db: Session = Depends(get_db),
) -> List[RankedMatchItem]:
    """Top-N viable matches for a surplus listing, ranked by score."""
    surplus = db.query(SurplusListing).filter(SurplusListing.id == surplus_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail=f"Surplus listing '{surplus_id}' not found.")

    demands = db.query(DemandListing).filter(
        DemandListing.status.in_([DemandStatus.OPEN, DemandStatus.PARTIALLY_MATCHED])
    ).all()

    results = [_run_match(surplus, d, db) for d in demands]
    viable  = sorted([r for r in results if r.is_viable], key=lambda r: -r.overall_score)
    top     = viable[:limit]

    demand_map = {d.id: d for d in demands}
    return [
        _result_to_ranked_item(i + 1, r, surplus, demand_map[r.demand_id], db)
        for i, r in enumerate(top)
    ]


@router.get(
    "/explain/{surplus_id}/{demand_id}",
    response_model=MatchResultResponse,
    summary="Detailed factor score breakdown for one surplus ↔ demand pair",
    description=(
        "Return the full factor-by-factor score breakdown and reasoning "
        "for a specific surplus ↔ demand pair. Useful for audit, transparency, and UI detail panels."
    ),
)
def explain_match(
    surplus_id: str,
    demand_id: str,
    db: Session = Depends(get_db),
) -> MatchResultResponse:
    """Full score breakdown for one specific surplus–demand pair."""
    surplus = db.query(SurplusListing).filter(SurplusListing.id == surplus_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail=f"Surplus listing '{surplus_id}' not found.")

    demand = db.query(DemandListing).filter(DemandListing.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail=f"Demand listing '{demand_id}' not found.")

    result = _run_match(surplus, demand, db)
    return _result_to_response(result)
