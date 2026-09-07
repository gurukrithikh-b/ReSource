"""
Compatibility Matching Scorer — Phase 3.3: Smart Compatibility Matching
=======================================================================
Deterministic, explainable scoring engine that evaluates pairwise compatibility
between a SurplusListing and a DemandListing.

Pipeline:
  surplus + demand + org coords
        ↓
  6 independent factor scorers (0–100 each)
        ↓
  weighted sum → overall match score (0–100, clamped, no negatives)
        ↓
  human-readable reason strings per factor
        ↓
  MatchResult dataclass (transparent, audit-friendly)

Factor weights (must sum to 100):
  category   25 pts  — category ID / name compatibility
  quantity   20 pts  — surplus remaining qty vs demand needed qty
  distance   20 pts  — haversine km between supplier and receiver
  time       20 pts  — expiry window vs required-by deadline
  urgency    10 pts  — demand urgency level bonus
  storage     5 pts  — storage condition compatibility

Hard disqualifiers (overall score forced to 0, match still returned for transparency):
  - Surplus is EXPIRED  (expires_at <= now)
  - Demand is FULFILLED (status == FULFILLED, or fulfilled_qty >= requested_qty)
  - Storage is completely incompatible (FROZEN surplus → receiver only supports AMBIENT)
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List

# ---------------------------------------------------------------------------
# Factor weight configuration
# ---------------------------------------------------------------------------
WEIGHTS = {
    "category": 25,
    "quantity":  20,
    "distance":  20,
    "time":      20,
    "urgency":   10,
    "storage":    5,
}
assert sum(WEIGHTS.values()) == 100, "Factor weights must sum to 100"

# Distance decay table: (km_threshold, score)
DISTANCE_DECAY = [
    (0,  100),
    (5,   95),
    (10,  85),
    (20,  70),
    (30,  55),
    (40,  35),
    (50,  15),
]
DISTANCE_MAX_KM = 50.0   # beyond this → distance score = 0, match is impractical

# Urgency ordinal scores
URGENCY_SCORES = {
    "CRITICAL": 100,
    "HIGH":      85,
    "MEDIUM":    60,
    "LOW":       35,
}

# Storage compatibility matrix: (surplus_storage → receiver_storage → score)
# FROZEN food can go to a FROZEN receiver only.
# REFRIGERATED food can go to REFRIGERATED or AMBIENT (temperature compatible).
# AMBIENT can go anywhere.
STORAGE_COMPAT = {
    "FROZEN":       {"FROZEN": 100, "REFRIGERATED":  0, "AMBIENT":  0},
    "REFRIGERATED": {"FROZEN":   0, "REFRIGERATED": 100, "AMBIENT": 70},
    "AMBIENT":      {"FROZEN":   0, "REFRIGERATED": 100, "AMBIENT": 100},
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class FactorDetail:
    """Score and human-readable reason for one matching factor."""
    score: float               # 0–100
    reason: str                # e.g. "Same resource category (Cooked Meals)"
    weight: int                # factor weight (unchanged from WEIGHTS)


@dataclass
class MatchResult:
    """
    Full compatibility match result for a surplus ↔ demand pair.

    `overall_score` is always in [0, 100]. It is 0 for disqualified pairs.
    `is_viable` is True only when overall_score > 0 and no hard disqualifier fired.
    `disqualification_reasons` lists why a score of 0 was assigned if applicable.
    """
    surplus_id:   str
    demand_id:    str
    overall_score: float                    # 0–100, rounded to 1 dp
    factor_scores: dict                     # {"category": 100, "quantity": 95, ...}
    factor_details: List[FactorDetail]      # full detail per factor
    reasons: List[str]                      # ordered human-readable reasons (positive first)
    is_viable: bool
    disqualification_reasons: List[str]     # empty list if viable
    distance_km: Optional[float]            # None if coords unavailable


# ---------------------------------------------------------------------------
# Haversine distance helper
# ---------------------------------------------------------------------------
def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres between two WGS-84 points."""
    R = 6371.0  # Earth radius km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _coords_valid(lat: Optional[float], lon: Optional[float]) -> bool:
    """Return True if coordinates look like real geographic data."""
    if lat is None or lon is None:
        return False
    # (0.0, 0.0) is the null-island sentinel — treat as missing
    if lat == 0.0 and lon == 0.0:
        return False
    return True


# ---------------------------------------------------------------------------
# Individual factor scorers
# ---------------------------------------------------------------------------

def _score_category(surplus_cat_id: str, demand_cat_id: str,
                    surplus_cat_name: str, demand_cat_name: str) -> FactorDetail:
    """
    Category compatibility:
      - Same category ID → 100 (exact match)
      - Different IDs but identical/overlapping names → 50 (partial)
      - No relationship → 0  ← triggers hard penalty
    """
    if surplus_cat_id and demand_cat_id and surplus_cat_id == demand_cat_id:
        return FactorDetail(
            score=100,
            reason=f"Same resource category ({surplus_cat_name or 'matched'})",
            weight=WEIGHTS["category"],
        )
    # Name-level similarity (simple substring check — both normalised)
    s_name = (surplus_cat_name or "").strip().lower()
    d_name = (demand_cat_name or "").strip().lower()
    if s_name and d_name and (s_name in d_name or d_name in s_name):
        return FactorDetail(
            score=50,
            reason=f"Related resource categories ({surplus_cat_name} ↔ {demand_cat_name})",
            weight=WEIGHTS["category"],
        )
    return FactorDetail(
        score=0,
        reason=f"Incompatible categories ({surplus_cat_name} vs {demand_cat_name})",
        weight=WEIGHTS["category"],
    )


def _score_quantity(remaining_qty: float, requested_qty: float,
                    fulfilled_qty: float) -> FactorDetail:
    """
    Quantity compatibility.
    needed = requested - already_fulfilled
    ratio  = min(remaining, needed) / needed   (capped 0–1)
    score  = ratio × 100
    """
    needed = max(0.0, requested_qty - fulfilled_qty)
    if needed <= 0:
        return FactorDetail(
            score=0,
            reason="Demand is already fully fulfilled — no additional quantity needed",
            weight=WEIGHTS["quantity"],
        )
    if remaining_qty <= 0:
        return FactorDetail(
            score=0,
            reason="No surplus remaining quantity available",
            weight=WEIGHTS["quantity"],
        )
    ratio = min(remaining_qty, needed) / needed
    score = round(ratio * 100, 1)
    if ratio >= 1.0:
        reason = f"Full quantity can be fulfilled ({remaining_qty:.1f} kg available ≥ {needed:.1f} kg needed)"
    elif ratio >= 0.5:
        reason = f"Partial fulfillment ({remaining_qty:.1f} kg covers {score:.0f}% of {needed:.1f} kg needed)"
    else:
        reason = f"Low quantity coverage ({remaining_qty:.1f} kg covers only {score:.0f}% of {needed:.1f} kg needed)"
    return FactorDetail(score=score, reason=reason, weight=WEIGHTS["quantity"])


def _score_distance(supplier_lat: Optional[float], supplier_lon: Optional[float],
                    receiver_lat: Optional[float], receiver_lon: Optional[float]) -> tuple:
    """
    Distance score.
    Returns (FactorDetail, distance_km_or_None).
    If either org has no valid coords → neutral score 50 (not 0, not misleading 100).
    """
    sup_valid = _coords_valid(supplier_lat, supplier_lon)
    rec_valid = _coords_valid(receiver_lat, receiver_lon)

    if not sup_valid or not rec_valid:
        return FactorDetail(
            score=50,
            reason="Location data unavailable — distance score is neutral",
            weight=WEIGHTS["distance"],
        ), None

    km = _haversine_km(supplier_lat, supplier_lon, receiver_lat, receiver_lon)
    km = round(km, 2)

    if km >= DISTANCE_MAX_KM:
        return FactorDetail(
            score=0,
            reason=f"Too far for practical delivery ({km:.1f} km — exceeds {DISTANCE_MAX_KM:.0f} km threshold)",
            weight=WEIGHTS["distance"],
        ), km

    # Interpolate between decay table breakpoints
    score = 0.0
    for i in range(len(DISTANCE_DECAY) - 1):
        km0, s0 = DISTANCE_DECAY[i]
        km1, s1 = DISTANCE_DECAY[i + 1]
        if km0 <= km <= km1:
            t = (km - km0) / (km1 - km0)
            score = s0 + t * (s1 - s0)
            break
    else:
        # km is between last breakpoint and DISTANCE_MAX_KM
        km0, s0 = DISTANCE_DECAY[-1]
        t = (km - km0) / (DISTANCE_MAX_KM - km0)
        score = s0 * (1 - t)

    score = round(max(0.0, min(100.0, score)), 1)

    if km <= 5:
        reason = f"Very close — only {km:.1f} km away"
    elif km <= 15:
        reason = f"Nearby receiver — {km:.1f} km away, easy delivery"
    elif km <= 30:
        reason = f"Moderate distance — {km:.1f} km, manageable delivery"
    else:
        reason = f"Longer distance — {km:.1f} km, feasible but reduces priority"

    return FactorDetail(score=score, reason=reason, weight=WEIGHTS["distance"]), km


def _score_time(expires_at: datetime, required_by: datetime, now: datetime) -> FactorDetail:
    """
    Time compatibility.
    - Expired surplus → 0
    - Expiry occurs before required_by and after now → score based on buffer
    - Expiry after required_by → 100 (resource will still be valid)
    """
    # Normalise to UTC-aware datetimes
    def _utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    now       = _utc(now)
    expires   = _utc(expires_at)
    req_by    = _utc(required_by)

    hours_to_expiry = (expires - now).total_seconds() / 3600

    if hours_to_expiry <= 0:
        return FactorDetail(
            score=0,
            reason="Surplus has already expired and cannot be redistributed",
            weight=WEIGHTS["time"],
        )

    # If surplus expires after required-by → always compatible
    if expires >= req_by:
        hours_until_req = max(0.0, (req_by - now).total_seconds() / 3600)
        if hours_until_req <= 0:
            return FactorDetail(
                score=60,
                reason="Surplus is available; demand deadline has just passed or is now",
                weight=WEIGHTS["time"],
            )
        return FactorDetail(
            score=100,
            reason=f"Surplus remains valid past the required-by deadline ({hours_to_expiry:.1f} hrs remaining)",
            weight=WEIGHTS["time"],
        )

    # Surplus expires before required-by — check if there's meaningful time left
    # Score degrades as expiry window shrinks relative to required-by
    hours_to_req = (req_by - now).total_seconds() / 3600
    if hours_to_req <= 0:
        return FactorDetail(
            score=40,
            reason="Demand deadline is imminent; any delivery will need to be immediate",
            weight=WEIGHTS["time"],
        )

    # Buffer: how much of the required-by window does the expiry cover?
    ratio = min(1.0, hours_to_expiry / max(hours_to_req, 0.1))
    score = round(40 + ratio * 60, 1)   # 40–100 range when surplus expires before req_by
    reason = (
        f"Surplus expires in {hours_to_expiry:.1f} hrs; demand needed within {hours_to_req:.1f} hrs — "
        f"{'adequate' if ratio >= 0.8 else 'tight'} window"
    )
    return FactorDetail(score=score, reason=reason, weight=WEIGHTS["time"])


def _score_urgency(urgency_level: str) -> FactorDetail:
    """Urgency bonus — higher urgency lifts the match priority."""
    level = (urgency_level or "MEDIUM").upper()
    score = URGENCY_SCORES.get(level, 60)
    labels = {
        "CRITICAL": "Critical priority demand — immediate redistribution needed",
        "HIGH":     "High priority demand — urgent redistribution recommended",
        "MEDIUM":   "Medium priority demand",
        "LOW":      "Low urgency demand",
    }
    return FactorDetail(
        score=float(score),
        reason=labels.get(level, "Medium priority demand"),
        weight=WEIGHTS["urgency"],
    )


def _score_storage(surplus_storage: str, demand_storage_capacity: str) -> FactorDetail:
    """
    Storage compatibility.
    surplus_storage: AMBIENT | REFRIGERATED | FROZEN (from StorageCondition enum)
    demand_storage_capacity: stored as a string; normalised to uppercase
    """
    s_storage = (surplus_storage or "AMBIENT").upper()
    d_capacity = (demand_storage_capacity or "AMBIENT").upper()

    # Normalise REFRIGERATED synonyms from older data
    for alias in ("REFRIGERATED", "FRIDGE", "CHILLED", "COLD"):
        if alias in d_capacity:
            d_capacity = "REFRIGERATED"
            break
    if "FROZEN" in d_capacity:
        d_capacity = "FROZEN"
    if d_capacity not in ("FROZEN", "REFRIGERATED", "AMBIENT"):
        d_capacity = "AMBIENT"

    compat = STORAGE_COMPAT.get(s_storage, {})
    score = float(compat.get(d_capacity, 0))

    if score == 100:
        reason = f"Storage requirements are fully compatible ({s_storage})"
    elif score > 0:
        reason = (
            f"Storage partially compatible — surplus is {s_storage}, "
            f"receiver capacity is {d_capacity}"
        )
    else:
        reason = (
            f"Storage INCOMPATIBLE — surplus requires {s_storage} "
            f"but receiver only supports {d_capacity}"
        )
    return FactorDetail(score=score, reason=reason, weight=WEIGHTS["storage"])


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_match(
    # Surplus fields
    surplus_id: str,
    surplus_cat_id: str,
    surplus_cat_name: str,
    surplus_remaining_qty: float,
    surplus_storage: str,
    surplus_expires_at: datetime,
    supplier_lat: Optional[float],
    supplier_lon: Optional[float],
    # Demand fields
    demand_id: str,
    demand_cat_id: str,
    demand_cat_name: str,
    demand_requested_qty: float,
    demand_fulfilled_qty: float,
    demand_storage_capacity: str,
    demand_urgency: str,
    demand_required_by: datetime,
    demand_status: str,
    receiver_lat: Optional[float],
    receiver_lon: Optional[float],
    # Optional override for testability
    now: Optional[datetime] = None,
) -> MatchResult:
    """
    Score one surplus ↔ demand pair across all 6 factors.

    Returns a fully populated MatchResult. Score is always 0–100.
    Disqualified matches have overall_score=0 and is_viable=False.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    disqualifiers: List[str] = []

    # --- Hard disqualification checks ---
    if _coords_valid(supplier_lat, supplier_lon):
        pass  # fine
    # Expired surplus
    exp = surplus_expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp <= now:
        disqualifiers.append("Surplus listing has expired")

    # Demand fully fulfilled
    needed = max(0.0, demand_requested_qty - demand_fulfilled_qty)
    if demand_status == "FULFILLED" or needed <= 0:
        disqualifiers.append("Demand is already fully fulfilled")

    # --- Compute all 6 factor scores ---
    cat_detail   = _score_category(surplus_cat_id, demand_cat_id,
                                   surplus_cat_name, demand_cat_name)
    qty_detail   = _score_quantity(surplus_remaining_qty, demand_requested_qty, demand_fulfilled_qty)
    dist_detail, distance_km = _score_distance(supplier_lat, supplier_lon,
                                               receiver_lat, receiver_lon)
    time_detail  = _score_time(surplus_expires_at, demand_required_by, now)
    urg_detail   = _score_urgency(demand_urgency)
    stor_detail  = _score_storage(surplus_storage, demand_storage_capacity)

    # Storage incompatibility is a hard disqualifier
    if stor_detail.score == 0 and "INCOMPATIBLE" in stor_detail.reason:
        disqualifiers.append(f"Storage incompatible: {stor_detail.reason}")

    # Category incompatibility is a hard disqualifier
    if cat_detail.score == 0:
        disqualifiers.append(f"Category mismatch: {cat_detail.reason}")

    factor_details = [cat_detail, qty_detail, dist_detail, time_detail, urg_detail, stor_detail]
    factor_keys    = ["category", "quantity", "distance", "time", "urgency", "storage"]

    if disqualifiers:
        # Return with zeroed score but full factor breakdown for transparency
        factor_scores = {k: d.score for k, d in zip(factor_keys, factor_details)}
        return MatchResult(
            surplus_id=surplus_id,
            demand_id=demand_id,
            overall_score=0.0,
            factor_scores=factor_scores,
            factor_details=factor_details,
            reasons=disqualifiers,
            is_viable=False,
            disqualification_reasons=disqualifiers,
            distance_km=distance_km,
        )

    # --- Weighted sum ---
    total_weight = sum(WEIGHTS.values())
    weighted_sum = sum(
        d.score * WEIGHTS[k]
        for k, d in zip(factor_keys, factor_details)
    )
    overall = round(max(0.0, min(100.0, weighted_sum / total_weight)), 1)

    factor_scores = {k: round(d.score, 1) for k, d in zip(factor_keys, factor_details)}

    # Build ordered reasons: best factors first (score desc), then lower ones
    sorted_details = sorted(zip(factor_keys, factor_details), key=lambda x: -x[1].score)
    reasons = [d.reason for _, d in sorted_details if d.reason]

    return MatchResult(
        surplus_id=surplus_id,
        demand_id=demand_id,
        overall_score=overall,
        factor_scores=factor_scores,
        factor_details=factor_details,
        reasons=reasons,
        is_viable=True,
        disqualification_reasons=[],
        distance_km=distance_km,
    )
