"""
Matching Schemas — Phase 3.3: Smart Compatibility Matching
==========================================================
Pydantic request/response models for the matching API endpoints.
Designed to carry enough information for a future Match Explorer frontend.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class FactorScores(BaseModel):
    """Per-factor compatibility scores (each 0–100)."""
    category: float = Field(..., description="Category compatibility score (0–100)")
    quantity: float = Field(..., description="Quantity coverage score (0–100)")
    distance: float = Field(..., description="Proximity score (0–100; 50 when location unknown)")
    time: float     = Field(..., description="Time-window compatibility score (0–100)")
    urgency: float  = Field(..., description="Demand urgency bonus score (0–100)")
    storage: float  = Field(..., description="Storage condition compatibility score (0–100)")


class FactorWeights(BaseModel):
    """Static factor weights used by the scoring engine."""
    category: int = 25
    quantity:  int = 20
    distance:  int = 20
    time:      int = 20
    urgency:   int = 10
    storage:   int = 5


class MatchResultResponse(BaseModel):
    """
    Full compatibility match result for one surplus ↔ demand pair.

    - `overall_score`  : 0–100 weighted composite score
    - `factor_scores`  : individual factor breakdown
    - `reasons`        : human-readable explanation strings (best factors first)
    - `is_viable`      : False if any hard disqualifier fired (expired, fulfilled, incompatible)
    - `disqualification_reasons`: non-empty when is_viable=False
    - `distance_km`    : haversine distance; null when coordinates unavailable

    Factor weights: category(25) + quantity(20) + distance(20) + time(20) + urgency(10) + storage(5) = 100
    """
    surplus_id:  str
    demand_id:   str
    overall_score: float = Field(..., ge=0, le=100, description="Weighted match score 0–100")
    factor_scores: FactorScores
    factor_weights: FactorWeights = Field(default_factory=FactorWeights)
    reasons: List[str] = Field(description="Human-readable explanation (best factors listed first)")
    is_viable: bool    = Field(description="True when no hard disqualifier applies")
    disqualification_reasons: List[str] = Field(default_factory=list)
    distance_km: Optional[float] = Field(None, description="Haversine km; null if location unavailable")


class RankedMatchItem(BaseModel):
    """
    A single ranked match entry, enriched with enough metadata for the Match Explorer UI.
    """
    rank: int
    surplus_id:   str
    demand_id:    str
    overall_score: float = Field(..., ge=0, le=100)
    factor_scores: FactorScores
    reasons: List[str]
    is_viable: bool
    disqualification_reasons: List[str] = Field(default_factory=list)
    distance_km: Optional[float] = None

    # Denormalised display fields (populated by endpoint from DB objects)
    surplus_title: Optional[str] = None
    surplus_quantity: Optional[float] = None
    surplus_unit: Optional[str] = None
    surplus_storage: Optional[str] = None
    surplus_expires_at: Optional[str] = None

    demand_title: Optional[str] = None
    demand_requested_quantity: Optional[float] = None
    demand_unit: Optional[str] = None
    demand_urgency: Optional[str] = None
    demand_required_by: Optional[str] = None
    demand_status: Optional[str] = None

    receiver_name: Optional[str] = None
    supplier_name: Optional[str] = None


class RankedMatchesResponse(BaseModel):
    """
    Ranked list of all matches for a given surplus or demand query.
    Matches are ordered by overall_score descending.
    Disqualified matches (is_viable=False) are included at the bottom for transparency.
    """
    query_type: str = Field(description="'surplus' or 'demand'")
    query_id:   str = Field(description="ID of the surplus or demand listing queried")
    total_candidates: int
    viable_count: int
    matches: List[RankedMatchItem]
