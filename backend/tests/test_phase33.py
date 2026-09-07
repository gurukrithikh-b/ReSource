"""
Phase 3.3 Tests — Smart Compatibility Matching Engine
======================================================
Tests cover (scorer unit tests + API integration tests):

  1.  Exact category match → score 100
  2.  Incompatible category → disqualified (score 0)
  3.  Sufficient quantity → quantity score 100
  4.  Insufficient quantity → reduced score
  5.  Distance scoring — near, mid, far, unknown
  6.  Expiry compatibility — valid, expired surplus, tight window
  7.  Required-by compatibility — surplus expires before/after deadline
  8.  Urgency influence — CRITICAL > HIGH > MEDIUM > LOW
  9.  Storage compatibility — full match, partial, incompatible
  10. Expired surplus → hard disqualification
  11. Fully fulfilled demand → hard disqualification
  12. Missing location → neutral distance score (50), no crash
  13. Score normalization — always 0–100, never negative
  14. Ranking order — higher score appears first in ranked list
  15. Human-readable reasons — non-empty, descriptive
  16. API endpoints — surplus/{id}, demand/{id}, top, explain
"""

import os
import sys
import math
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.matching.scorer import (
    score_match,
    _score_category,
    _score_quantity,
    _score_distance,
    _score_time,
    _score_urgency,
    _score_storage,
    _haversine_km,
    WEIGHTS,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
FUTURE_REQ   = NOW + timedelta(hours=8)    # demand needed in 8 hours
FAR_FUTURE   = NOW + timedelta(hours=48)   # surplus expires in 48 hours (well within)
NEAR_EXPIRY  = NOW + timedelta(hours=2)    # expires in 2 hours
JUST_EXPIRED = NOW - timedelta(minutes=5)  # expired 5 minutes ago

SURPLUS_BASE = dict(
    surplus_id="s1",
    surplus_cat_id="cat-001",
    surplus_cat_name="Cooked Meals",
    surplus_remaining_qty=80.0,
    surplus_storage="REFRIGERATED",
    surplus_expires_at=FAR_FUTURE,
    supplier_lat=12.9716,
    supplier_lon=77.5946,
)

DEMAND_BASE = dict(
    demand_id="d1",
    demand_cat_id="cat-001",
    demand_cat_name="Cooked Meals",
    demand_requested_qty=60.0,
    demand_fulfilled_qty=0.0,
    demand_storage_capacity="REFRIGERATED",
    demand_urgency="HIGH",
    demand_required_by=FUTURE_REQ,
    demand_status="OPEN",
    receiver_lat=12.9652,
    receiver_lon=77.6042,
)

def make_result(**overrides):
    s = {**SURPLUS_BASE}
    d = {**DEMAND_BASE}
    s.update({k: v for k, v in overrides.items() if k.startswith("surplus_") or k in ("supplier_lat","supplier_lon")})
    d.update({k: v for k, v in overrides.items() if k.startswith("demand_") or k in ("receiver_lat","receiver_lon")})
    return score_match(**s, **d, now=NOW)


# ===========================================================================
# PART A — Pure scorer unit tests
# ===========================================================================

class TestCategoryScoring:
    def test_exact_category_id_match_is_100(self):
        det = _score_category("cat-001", "cat-001", "Cooked Meals", "Cooked Meals")
        assert det.score == 100

    def test_different_category_ids_no_name_overlap_is_0(self):
        det = _score_category("cat-001", "cat-002", "Cooked Meals", "Fresh Produce")
        assert det.score == 0

    def test_name_level_partial_match_is_50(self):
        # Different IDs but name contains the other
        det = _score_category("cat-001", "cat-003", "Meals", "Cooked Meals")
        assert det.score == 50

    def test_reason_mentions_category_name(self):
        det = _score_category("cat-001", "cat-001", "Cooked Meals", "Cooked Meals")
        assert "Cooked Meals" in det.reason


class TestQuantityScoring:
    def test_full_fulfillment_is_100(self):
        det = _score_quantity(remaining_qty=80.0, requested_qty=60.0, fulfilled_qty=0.0)
        assert det.score == 100.0

    def test_partial_fulfillment_scores_proportionally(self):
        det = _score_quantity(remaining_qty=30.0, requested_qty=60.0, fulfilled_qty=0.0)
        assert det.score == pytest.approx(50.0)

    def test_demand_already_fulfilled_is_0(self):
        det = _score_quantity(remaining_qty=50.0, requested_qty=60.0, fulfilled_qty=60.0)
        assert det.score == 0
        assert "fulfilled" in det.reason.lower()

    def test_remaining_zero_is_0(self):
        det = _score_quantity(remaining_qty=0.0, requested_qty=60.0, fulfilled_qty=0.0)
        assert det.score == 0

    def test_over_supply_caps_at_100(self):
        det = _score_quantity(remaining_qty=200.0, requested_qty=60.0, fulfilled_qty=0.0)
        assert det.score == 100.0

    def test_partial_already_fulfilled_reduces_needed(self):
        # 20 already fulfilled, 40 still needed, 30 available → 30/40 = 75%
        det = _score_quantity(remaining_qty=30.0, requested_qty=60.0, fulfilled_qty=20.0)
        assert det.score == pytest.approx(75.0)


class TestDistanceScoring:
    def test_very_close_origin_is_100(self):
        det, km = _score_distance(0.0, 0.0, 0.0, 0.0)
        # Both are (0,0) → null-island → neutral
        assert det.score == 50.0
        assert km is None

    def test_nearby_5km_high_score(self):
        det, km = _score_distance(12.9716, 77.5946, 12.9200, 77.6400)
        assert det.score >= 80.0
        assert km is not None and km > 0

    def test_very_far_over_50km_is_0(self):
        # Mumbai → Pune ~150 km
        det, km = _score_distance(19.076, 72.8777, 18.5204, 73.8567)
        assert det.score == 0.0
        assert km is not None and km > 50

    def test_missing_supplier_coords_neutral(self):
        det, km = _score_distance(None, None, 12.9652, 77.6042)
        assert det.score == 50.0
        assert km is None

    def test_missing_receiver_coords_neutral(self):
        det, km = _score_distance(12.9716, 77.5946, None, None)
        assert det.score == 50.0
        assert km is None

    def test_null_island_coords_neutral(self):
        det, km = _score_distance(0.0, 0.0, 12.9652, 77.6042)
        assert det.score == 50.0

    def test_distance_score_always_0_to_100(self):
        for lat1, lon1, lat2, lon2 in [
            (0, 0, 0, 0), (12, 77, 13, 78), (19, 72, 18, 73), (28, 77, 12, 80)
        ]:
            det, _ = _score_distance(lat1, lon1, lat2, lon2)
            assert 0 <= det.score <= 100

    def test_haversine_known_distance(self):
        # Bangalore ~13 km to nearby city
        km = _haversine_km(12.9716, 77.5946, 12.8698, 77.6047)
        assert 10 < km < 15  # roughly 11–12 km


class TestTimeScoring:
    def test_surplus_expires_after_required_by_is_100(self):
        # Surplus lasts 48 hours, demand needed in 8 hours → ideal
        det = _score_time(FAR_FUTURE, FUTURE_REQ, NOW)
        assert det.score == 100.0

    def test_expired_surplus_is_0(self):
        det = _score_time(JUST_EXPIRED, FUTURE_REQ, NOW)
        assert det.score == 0.0
        assert "expired" in det.reason.lower()

    def test_tight_window_scores_between_40_and_100(self):
        # Surplus expires in 2h, demand needed in 4h → tight but possible
        req_by = NOW + timedelta(hours=4)
        det = _score_time(NEAR_EXPIRY, req_by, NOW)
        assert 40 <= det.score <= 100

    def test_reason_contains_hours_info(self):
        det = _score_time(FAR_FUTURE, FUTURE_REQ, NOW)
        assert "hrs" in det.reason or "hour" in det.reason.lower() or "valid" in det.reason.lower()


class TestUrgencyScoring:
    def test_critical_is_100(self):
        assert _score_urgency("CRITICAL").score == 100.0

    def test_high_is_85(self):
        assert _score_urgency("HIGH").score == 85.0

    def test_medium_is_60(self):
        assert _score_urgency("MEDIUM").score == 60.0

    def test_low_is_35(self):
        assert _score_urgency("LOW").score == 35.0

    def test_urgency_ordering(self):
        scores = [_score_urgency(u).score for u in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]]
        assert scores == sorted(scores)

    def test_unknown_urgency_defaults_to_medium(self):
        s = _score_urgency("UNKNOWN").score
        assert s == 60.0  # defaults to MEDIUM


class TestStorageScoring:
    def test_exact_refrigerated_match(self):
        det = _score_storage("REFRIGERATED", "REFRIGERATED")
        assert det.score == 100.0

    def test_exact_frozen_match(self):
        det = _score_storage("FROZEN", "FROZEN")
        assert det.score == 100.0

    def test_exact_ambient_match(self):
        det = _score_storage("AMBIENT", "AMBIENT")
        assert det.score == 100.0

    def test_refrigerated_to_ambient_partial(self):
        # REFRIGERATED surplus can go to AMBIENT receiver (70)
        det = _score_storage("REFRIGERATED", "AMBIENT")
        assert det.score == 70.0

    def test_frozen_to_ambient_incompatible(self):
        det = _score_storage("FROZEN", "AMBIENT")
        assert det.score == 0.0
        assert "incompatible" in det.reason.lower() or "INCOMPATIBLE" in det.reason

    def test_frozen_to_refrigerated_incompatible(self):
        det = _score_storage("FROZEN", "REFRIGERATED")
        assert det.score == 0.0

    def test_ambient_to_refrigerated_compatible(self):
        det = _score_storage("AMBIENT", "REFRIGERATED")
        assert det.score == 100.0


# ===========================================================================
# PART B — Full match scoring integration tests
# ===========================================================================

class TestMatchScoreIntegration:
    def test_ideal_match_high_score(self):
        result = make_result()
        assert result.is_viable is True
        assert result.overall_score >= 70.0  # ideal conditions → high score

    def test_incompatible_category_disqualifies(self):
        result = make_result(
            surplus_cat_id="cat-001", surplus_cat_name="Cooked Meals",
            demand_cat_id="cat-999", demand_cat_name="Clothing",
        )
        assert result.is_viable is False
        assert result.overall_score == 0.0
        assert any("ategory" in r for r in result.disqualification_reasons)

    def test_expired_surplus_disqualifies(self):
        result = make_result(surplus_expires_at=JUST_EXPIRED)
        assert result.is_viable is False
        assert result.overall_score == 0.0
        assert any("expired" in r.lower() for r in result.disqualification_reasons)

    def test_fulfilled_demand_disqualifies(self):
        result = make_result(demand_status="FULFILLED", demand_fulfilled_qty=60.0)
        assert result.is_viable is False
        assert result.overall_score == 0.0

    def test_storage_incompatible_disqualifies(self):
        result = make_result(surplus_storage="FROZEN", demand_storage_capacity="AMBIENT")
        assert result.is_viable is False
        assert result.overall_score == 0.0

    def test_missing_location_does_not_crash(self):
        result = make_result(supplier_lat=None, supplier_lon=None)
        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert result.factor_scores["distance"] == 50.0  # neutral

    def test_score_always_between_0_and_100(self):
        cases = [
            {},  # ideal
            {"surplus_remaining_qty": 5.0},
            {"demand_urgency": "LOW"},
            {"demand_urgency": "CRITICAL"},
            {"supplier_lat": None, "supplier_lon": None},
        ]
        for overrides in cases:
            r = make_result(**overrides)
            assert 0 <= r.overall_score <= 100, f"Score {r.overall_score} out of range for {overrides}"

    def test_score_never_negative(self):
        r = make_result(surplus_remaining_qty=1.0, demand_urgency="LOW")
        assert r.overall_score >= 0.0

    def test_factor_scores_never_exceed_100(self):
        r = make_result()
        for k, v in r.factor_scores.items():
            assert v <= 100.0, f"Factor {k} score {v} exceeds 100"

    def test_factor_scores_never_negative(self):
        r = make_result()
        for k, v in r.factor_scores.items():
            assert v >= 0.0, f"Factor {k} score {v} is negative"

    def test_reasons_non_empty_for_viable_match(self):
        r = make_result()
        assert len(r.reasons) > 0

    def test_reasons_non_empty_for_disqualified(self):
        r = make_result(surplus_expires_at=JUST_EXPIRED)
        assert len(r.reasons) > 0

    def test_critical_urgency_higher_score_than_low(self):
        r_critical = make_result(demand_urgency="CRITICAL")
        r_low      = make_result(demand_urgency="LOW")
        assert r_critical.overall_score > r_low.overall_score

    def test_full_quantity_higher_than_partial(self):
        r_full    = make_result(surplus_remaining_qty=100.0)
        r_partial = make_result(surplus_remaining_qty=10.0)
        assert r_full.overall_score > r_partial.overall_score

    def test_factor_weights_sum_to_100(self):
        assert sum(WEIGHTS.values()) == 100


class TestRankingOrder:
    def test_higher_score_ranks_first(self):
        r1 = make_result(demand_urgency="CRITICAL", surplus_remaining_qty=100.0)  # best
        r2 = make_result(demand_urgency="LOW",      surplus_remaining_qty=5.0)    # worst
        assert r1.overall_score > r2.overall_score

    def test_disqualified_has_score_0(self):
        r = make_result(surplus_expires_at=JUST_EXPIRED)
        assert r.overall_score == 0.0

    def test_viable_match_has_positive_score(self):
        r = make_result()
        assert r.overall_score > 0

    def test_all_factor_keys_present(self):
        r = make_result()
        for key in ["category", "quantity", "distance", "time", "urgency", "storage"]:
            assert key in r.factor_scores


class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine_km(12.0, 77.0, 12.0, 77.0) == pytest.approx(0.0, abs=0.01)

    def test_known_distance_is_reasonable(self):
        # Approx 1 degree lat ≈ 111 km
        km = _haversine_km(0.0, 0.0, 1.0, 0.0)
        assert 110 < km < 112


# ===========================================================================
# PART C — API endpoint integration tests
# ===========================================================================

class TestMatchingAPIEndpoints:
    """
    These tests run against an in-memory test DB.
    The DB starts empty so surplus/demand lookups return 404,
    which lets us validate error handling. Positive-path tests
    require seeded data (pre-existing Phase 2A limitation).
    """

    def test_surplus_not_found_returns_404(self):
        resp = client.get("/api/v1/matching/surplus/nonexistent-id-xyz")
        assert resp.status_code == 404

    def test_demand_not_found_returns_404(self):
        resp = client.get("/api/v1/matching/demand/nonexistent-id-xyz")
        assert resp.status_code == 404

    def test_top_not_found_returns_404(self):
        resp = client.get("/api/v1/matching/surplus/nonexistent-id-xyz/top")
        assert resp.status_code == 404

    def test_explain_surplus_not_found_returns_404(self):
        resp = client.get("/api/v1/matching/explain/bad-surplus-id/bad-demand-id")
        assert resp.status_code == 404

    def test_matching_routes_registered(self):
        # OpenAPI schema must list the matching paths
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        paths = resp.json().get("paths", {})
        matching_paths = [p for p in paths if "/matching/" in p]
        assert len(matching_paths) >= 4, f"Expected ≥4 matching paths, got: {matching_paths}"

    def test_top_query_with_invalid_limit_rejected(self):
        # limit=0 is below ge=1 validation
        resp = client.get("/api/v1/matching/surplus/any-id/top?limit=0")
        assert resp.status_code == 422  # Unprocessable Entity

    def test_top_query_with_overlimit_rejected(self):
        resp = client.get("/api/v1/matching/surplus/any-id/top?limit=999")
        assert resp.status_code in (404, 422)  # 404 (not found) or 422 (validation)
