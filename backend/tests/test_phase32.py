"""
Phase 3.2 Tests — Predictive Supply & Demand Engine
=====================================================
Tests cover:
  1.  Dataset loading (surplus & demand CSVs exist and parse correctly)
  2.  Feature generation (correct columns, correct shapes, no leakage)
  3.  Model training (runs without error, sets is_trained flag)
  4.  Prediction output format (required keys present)
  5.  Positive/valid numeric predictions (predicted_quantity_kg >= 0)
  6.  MAE/RMSE calculation (real floats, not hard-coded; mae >= 0, rmse >= mae)
  7.  Time-based validation (train dates strictly before validation dates)
  8.  API endpoints — surplus, demand, forecast, metrics, retrain
"""

import os
import sys
import math
import pytest
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to sys.path so imports resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

# ML modules (train / predict logic)
from app.ml.surplus_predictor import (
    SurplusPredictor,
    _build_features as _build_surplus_features,
    FEATURE_COLS as SURPLUS_FEATURE_COLS,
    SURPLUS_CSV,
)
from app.ml.demand_predictor import (
    DemandPredictor,
    _build_demand_features,
    FEATURE_COLS as DEMAND_FEATURE_COLS,
    DEMAND_CSV,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures — train fresh predictors for each test module session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def surplus_pred() -> SurplusPredictor:
    """Return a trained SurplusPredictor (trained once per test session)."""
    p = SurplusPredictor.__new__(SurplusPredictor)
    from sklearn.preprocessing import LabelEncoder
    p.model = None
    p.org_enc = LabelEncoder()
    p.cat_enc = LabelEncoder()
    p.is_trained = False
    p.metrics = {}
    p.train_date_min = p.train_date_max = None
    p.val_date_min = p.val_date_max = None
    p.train_rows = p.val_rows = 0
    p.known_orgs = []
    p.known_cats = []
    p.train()
    return p


@pytest.fixture(scope="module")
def demand_pred() -> DemandPredictor:
    """Return a trained DemandPredictor (trained once per test session)."""
    p = DemandPredictor.__new__(DemandPredictor)
    from sklearn.preprocessing import LabelEncoder
    p.model = None
    p.org_enc = LabelEncoder()
    p.cat_enc = LabelEncoder()
    p.is_trained = False
    p.metrics = {}
    p.train_date_min = p.train_date_max = None
    p.val_date_min = p.val_date_max = None
    p.train_rows = p.val_rows = 0
    p.known_orgs = []
    p.known_cats = []
    p.train()
    return p


# ===========================================================================
# 1. Dataset loading
# ===========================================================================

class TestDatasetLoading:
    def test_surplus_csv_exists(self):
        """historical_surplus.csv must be present."""
        assert SURPLUS_CSV.exists(), f"Missing: {SURPLUS_CSV}"

    def test_demand_csv_exists(self):
        """historical_demand.csv must be present."""
        assert DEMAND_CSV.exists(), f"Missing: {DEMAND_CSV}"

    def test_surplus_csv_loads_correctly(self):
        """Surplus CSV must parse without error and contain expected columns."""
        df = pd.read_csv(SURPLUS_CSV)
        assert len(df) > 0, "Surplus CSV is empty"
        for col in ["date", "organization_id", "category", "quantity", "is_event_day", "day_of_week"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_demand_csv_loads_correctly(self):
        """Demand CSV must parse without error and contain expected columns."""
        df = pd.read_csv(DEMAND_CSV)
        assert len(df) > 0, "Demand CSV is empty"
        for col in ["date", "organization_id", "category", "requested_quantity", "is_event_day", "day_of_week"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_surplus_date_range(self):
        """Surplus data should span Jan 2025 to Dec 2025."""
        df = pd.read_csv(SURPLUS_CSV, parse_dates=["date"])
        assert df["date"].min() <= pd.Timestamp("2025-01-31")
        assert df["date"].max() >= pd.Timestamp("2025-12-01")

    def test_demand_date_range(self):
        """Demand data should span Jan 2025 to Dec 2025."""
        df = pd.read_csv(DEMAND_CSV, parse_dates=["date"])
        assert df["date"].min() <= pd.Timestamp("2025-01-31")
        assert df["date"].max() >= pd.Timestamp("2025-12-01")


# ===========================================================================
# 2. Feature generation
# ===========================================================================

class TestFeatureGeneration:
    def test_surplus_features_have_correct_columns(self):
        """After feature engineering all FEATURE_COLS must be present."""
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(SURPLUS_CSV)
        feat = _build_surplus_features(df, LabelEncoder(), LabelEncoder(), is_training=True)
        for col in SURPLUS_FEATURE_COLS:
            assert col in feat.columns, f"Missing feature column: {col}"

    def test_demand_features_have_correct_columns(self):
        """After feature engineering all FEATURE_COLS must be present."""
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(DEMAND_CSV)
        feat = _build_demand_features(df, LabelEncoder(), LabelEncoder(), is_training=True)
        for col in DEMAND_FEATURE_COLS:
            assert col in feat.columns, f"Missing feature column: {col}"

    def test_surplus_day_of_week_encoded(self):
        """day_of_week_num should be an integer in [0, 6]."""
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(SURPLUS_CSV)
        feat = _build_surplus_features(df, LabelEncoder(), LabelEncoder(), is_training=True)
        assert feat["day_of_week_num"].between(0, 6).all()

    def test_surplus_is_event_day_binary(self):
        """is_event_day feature must be 0 or 1 only."""
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(SURPLUS_CSV)
        feat = _build_surplus_features(df, LabelEncoder(), LabelEncoder(), is_training=True)
        assert set(feat["is_event_day"].unique()).issubset({0, 1})

    def test_lag_does_not_leak_current_day(self):
        """lag_7 uses shift(7); it must NOT equal the current row's quantity."""
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(SURPLUS_CSV)
        feat = _build_surplus_features(df, LabelEncoder(), LabelEncoder(), is_training=True)
        # Where lag_7 is not NaN, it should not universally equal quantity
        valid = feat.dropna(subset=["lag_7"])
        # There must exist some row where lag_7 != quantity (i.e. no leakage)
        assert (valid["lag_7"] != valid["quantity"]).any()


# ===========================================================================
# 3. Model training
# ===========================================================================

class TestModelTraining:
    def test_surplus_trains_without_error(self, surplus_pred):
        assert surplus_pred.is_trained is True

    def test_demand_trains_without_error(self, demand_pred):
        assert demand_pred.is_trained is True

    def test_surplus_has_positive_train_rows(self, surplus_pred):
        assert surplus_pred.train_rows > 0

    def test_demand_has_positive_train_rows(self, demand_pred):
        assert demand_pred.train_rows > 0

    def test_surplus_has_positive_val_rows(self, surplus_pred):
        assert surplus_pred.val_rows > 0

    def test_demand_has_positive_val_rows(self, demand_pred):
        assert demand_pred.val_rows > 0

    def test_surplus_model_not_none(self, surplus_pred):
        assert surplus_pred.model is not None

    def test_demand_model_not_none(self, demand_pred):
        assert demand_pred.model is not None


# ===========================================================================
# 4. Prediction output format
# ===========================================================================

class TestPredictionOutputFormat:
    SURPLUS_ORG = "hist-sup-001"
    DEMAND_ORG  = "hist-rec-001"
    CATEGORY    = "Cooked Meals"
    DATE        = "2026-03-15"

    def test_surplus_prediction_keys(self, surplus_pred):
        result = surplus_pred.predict(self.SURPLUS_ORG, self.CATEGORY, self.DATE)
        for key in ["organization_id", "category", "target_date",
                    "predicted_quantity_kg", "model", "prediction_type",
                    "data_disclaimer", "metrics"]:
            assert key in result, f"Missing key: {key}"

    def test_demand_prediction_keys(self, demand_pred):
        result = demand_pred.predict(self.DEMAND_ORG, self.CATEGORY, self.DATE)
        for key in ["organization_id", "category", "target_date",
                    "predicted_quantity_kg", "model", "prediction_type",
                    "data_disclaimer", "metrics"]:
            assert key in result, f"Missing key: {key}"

    def test_surplus_prediction_type_label(self, surplus_pred):
        result = surplus_pred.predict(self.SURPLUS_ORG, self.CATEGORY, self.DATE)
        assert result["prediction_type"] == "surplus"

    def test_demand_prediction_type_label(self, demand_pred):
        result = demand_pred.predict(self.DEMAND_ORG, self.CATEGORY, self.DATE)
        assert result["prediction_type"] == "demand"

    def test_disclaimer_present_in_surplus(self, surplus_pred):
        result = surplus_pred.predict(self.SURPLUS_ORG, self.CATEGORY, self.DATE)
        assert "SYNTHETIC" in result["data_disclaimer"].upper() or "MODEL" in result["data_disclaimer"].upper()

    def test_disclaimer_present_in_demand(self, demand_pred):
        result = demand_pred.predict(self.DEMAND_ORG, self.CATEGORY, self.DATE)
        assert "SYNTHETIC" in result["data_disclaimer"].upper() or "MODEL" in result["data_disclaimer"].upper()


# ===========================================================================
# 5. Positive / valid numeric predictions
# ===========================================================================

class TestPositiveNumericPredictions:
    SURPLUS_ORG = "hist-sup-001"
    DEMAND_ORG  = "hist-rec-001"
    CATEGORY    = "Cooked Meals"
    DATE        = "2026-06-10"

    def test_surplus_prediction_is_non_negative(self, surplus_pred):
        result = surplus_pred.predict(self.SURPLUS_ORG, self.CATEGORY, self.DATE)
        assert result["predicted_quantity_kg"] >= 0.0

    def test_demand_prediction_is_non_negative(self, demand_pred):
        result = demand_pred.predict(self.DEMAND_ORG, self.CATEGORY, self.DATE)
        assert result["predicted_quantity_kg"] >= 0.0

    def test_surplus_prediction_is_finite(self, surplus_pred):
        result = surplus_pred.predict(self.SURPLUS_ORG, self.CATEGORY, self.DATE)
        assert math.isfinite(result["predicted_quantity_kg"])

    def test_demand_prediction_is_finite(self, demand_pred):
        result = demand_pred.predict(self.DEMAND_ORG, self.CATEGORY, self.DATE)
        assert math.isfinite(result["predicted_quantity_kg"])

    def test_surplus_unknown_org_still_predicts(self, surplus_pred):
        """Prediction should not crash for unknown org (uses global fallback)."""
        result = surplus_pred.predict("unknown-org-999", "Cooked Meals", self.DATE)
        assert result["predicted_quantity_kg"] >= 0.0

    def test_demand_unknown_org_still_predicts(self, demand_pred):
        """Prediction should not crash for unknown org (uses global fallback)."""
        result = demand_pred.predict("unknown-org-999", "Cooked Meals", self.DATE)
        assert result["predicted_quantity_kg"] >= 0.0


# ===========================================================================
# 6. MAE / RMSE calculation
# ===========================================================================

class TestMetrics:
    def test_surplus_mae_is_positive(self, surplus_pred):
        assert surplus_pred.metrics["mae"] >= 0.0

    def test_surplus_rmse_is_positive(self, surplus_pred):
        assert surplus_pred.metrics["rmse"] >= 0.0

    def test_surplus_rmse_gte_mae(self, surplus_pred):
        """RMSE >= MAE is always true (Cauchy–Schwarz inequality)."""
        assert surplus_pred.metrics["rmse"] >= surplus_pred.metrics["mae"] - 1e-6

    def test_demand_mae_is_positive(self, demand_pred):
        assert demand_pred.metrics["mae"] >= 0.0

    def test_demand_rmse_is_positive(self, demand_pred):
        assert demand_pred.metrics["rmse"] >= 0.0

    def test_demand_rmse_gte_mae(self, demand_pred):
        assert demand_pred.metrics["rmse"] >= demand_pred.metrics["mae"] - 1e-6

    def test_surplus_mae_not_hard_coded(self, surplus_pred):
        """MAE must be a real computed float, not an obviously hard-coded value."""
        mae = surplus_pred.metrics["mae"]
        assert isinstance(mae, float)
        assert mae != 0.0 or surplus_pred.val_rows == 0  # 0.0 only if val is empty (impossible)

    def test_demand_mae_not_hard_coded(self, demand_pred):
        mae = demand_pred.metrics["mae"]
        assert isinstance(mae, float)
        assert mae != 0.0 or demand_pred.val_rows == 0


# ===========================================================================
# 7. Time-based validation (train before val)
# ===========================================================================

class TestTimeBasedValidation:
    def test_surplus_train_date_before_val_date(self, surplus_pred):
        """Train set must end before the validation set begins."""
        train_end = pd.Timestamp(surplus_pred.train_date_max)
        val_start = pd.Timestamp(surplus_pred.val_date_min)
        assert train_end <= val_start, (
            f"Leakage: train ends {train_end}, val starts {val_start}"
        )

    def test_demand_train_date_before_val_date(self, demand_pred):
        val_start = pd.Timestamp(demand_pred.val_date_min)
        train_end = pd.Timestamp(demand_pred.train_date_max)
        assert train_end <= val_start, (
            f"Leakage: train ends {train_end}, val starts {val_start}"
        )

    def test_surplus_split_proportions(self, surplus_pred):
        """Train set should be approximately 75 % of total rows."""
        total = surplus_pred.train_rows + surplus_pred.val_rows
        train_pct = surplus_pred.train_rows / total
        assert 0.70 <= train_pct <= 0.80, f"Unexpected split ratio: {train_pct:.2f}"

    def test_demand_split_proportions(self, demand_pred):
        total = demand_pred.train_rows + demand_pred.val_rows
        train_pct = demand_pred.train_rows / total
        assert 0.70 <= train_pct <= 0.80, f"Unexpected split ratio: {train_pct:.2f}"


# ===========================================================================
# 8. API endpoint tests
# ===========================================================================

class TestPredictionAPIEndpoints:
    """Integration tests against the FastAPI TestClient."""

    # --- POST /predictions/surplus ---
    def test_post_surplus_prediction_returns_200(self):
        payload = {
            "organization_id": "hist-sup-001",
            "category": "Cooked Meals",
            "target_date": "2026-04-15",
            "is_event_day": False,
        }
        resp = client.post("/api/v1/predictions/surplus", json=payload)
        assert resp.status_code == 200

    def test_post_surplus_prediction_structure(self):
        payload = {
            "organization_id": "hist-sup-001",
            "category": "Cooked Meals",
            "target_date": "2026-04-15",
        }
        resp = client.post("/api/v1/predictions/surplus", json=payload)
        data = resp.json()
        assert "predicted_quantity_kg" in data
        assert data["predicted_quantity_kg"] >= 0.0
        assert data["prediction_type"] == "surplus"

    def test_post_surplus_has_disclaimer(self):
        payload = {
            "organization_id": "hist-sup-001",
            "category": "Cooked Meals",
            "target_date": "2026-04-15",
        }
        resp = client.post("/api/v1/predictions/surplus", json=payload)
        data = resp.json()
        disclaimer = data.get("data_disclaimer", "")
        assert len(disclaimer) > 0

    # --- POST /predictions/demand ---
    def test_post_demand_prediction_returns_200(self):
        payload = {
            "organization_id": "hist-rec-001",
            "category": "Cooked Meals",
            "target_date": "2026-04-15",
        }
        resp = client.post("/api/v1/predictions/demand", json=payload)
        assert resp.status_code == 200

    def test_post_demand_prediction_structure(self):
        payload = {
            "organization_id": "hist-rec-001",
            "category": "Cooked Meals",
            "target_date": "2026-04-15",
        }
        resp = client.post("/api/v1/predictions/demand", json=payload)
        data = resp.json()
        assert "predicted_quantity_kg" in data
        assert data["predicted_quantity_kg"] >= 0.0
        assert data["prediction_type"] == "demand"

    # --- POST /predictions/surplus/forecast ---
    def test_surplus_forecast_returns_correct_num_days(self):
        payload = {
            "organization_id": "hist-sup-001",
            "category": "Cooked Meals",
            "start_date": "2026-04-01",
            "days": 5,
        }
        resp = client.post("/api/v1/predictions/surplus/forecast", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["forecasts"]) == 5

    def test_demand_forecast_returns_correct_num_days(self):
        payload = {
            "organization_id": "hist-rec-001",
            "category": "Cooked Meals",
            "start_date": "2026-04-01",
            "days": 3,
        }
        resp = client.post("/api/v1/predictions/demand/forecast", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["forecasts"]) == 3

    # --- GET /predictions/metrics ---
    def test_get_combined_metrics_returns_200(self):
        resp = client.get("/api/v1/predictions/metrics")
        assert resp.status_code == 200

    def test_get_combined_metrics_has_surplus_and_demand(self):
        resp = client.get("/api/v1/predictions/metrics")
        data = resp.json()
        assert "surplus" in data
        assert "demand" in data

    def test_surplus_metrics_mae_and_rmse_positive(self):
        resp = client.get("/api/v1/predictions/metrics/surplus")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metrics"]["mae"] >= 0.0
        assert data["metrics"]["rmse"] >= 0.0

    def test_demand_metrics_mae_and_rmse_positive(self):
        resp = client.get("/api/v1/predictions/metrics/demand")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metrics"]["mae"] >= 0.0
        assert data["metrics"]["rmse"] >= 0.0

    def test_metrics_contain_training_date_range(self):
        resp = client.get("/api/v1/predictions/metrics/surplus")
        data = resp.json()
        assert "train_date_range" in data
        assert len(data["train_date_range"]) == 2

    def test_metrics_contain_feature_list(self):
        resp = client.get("/api/v1/predictions/metrics/surplus")
        data = resp.json()
        assert "features" in data
        assert len(data["features"]) > 0

    def test_metrics_known_orgs_and_cats_nonempty(self):
        resp = client.get("/api/v1/predictions/metrics/surplus")
        data = resp.json()
        assert len(data["known_orgs"]) > 0
        assert len(data["known_cats"]) > 0

    def test_metrics_disclaimer_present(self):
        resp = client.get("/api/v1/predictions/metrics")
        data = resp.json()
        disclaimer = data["surplus"].get("data_disclaimer", "")
        assert len(disclaimer) > 0

    # --- Batch forecast all predictions non-negative ---
    def test_all_forecast_predictions_non_negative(self):
        payload = {
            "organization_id": "hist-sup-002",
            "category": "Cooked Meals",
            "start_date": "2026-01-01",
            "days": 7,
        }
        resp = client.post("/api/v1/predictions/surplus/forecast", json=payload)
        assert resp.status_code == 200
        for item in resp.json()["forecasts"]:
            assert item["predicted_quantity_kg"] >= 0.0
