"""
Surplus Predictor — Phase 3.2: Predictive Supply & Demand Engine
================================================================
Pipeline summary:
  1. LOAD  — Read historical_surplus.csv (synthetic, Jan–Dec 2025)
  2. FEATURES — Engineer temporal + categorical + lag/rolling features
               (day_of_week_num, day_of_month, month, org_encoded, cat_encoded,
                is_event_day, is_weekend, rolling_7d_mean, rolling_7d_std, lag_7)
  3. SPLIT — TIME-BASED split: train on first 75 % of dates, validate on last 25 %
             NO random shuffling — preserves temporal ordering, avoids leakage
  4. TRAIN — RandomForestRegressor (n_estimators=150, max_depth=12, random_state=42)
  5. EVALUATE — MAE and RMSE on the validation set (real metrics, never hard-coded)
  6. PREDICT — Predict future quantities given org / category / date inputs

NOTE: All data is SYNTHETIC (is_simulated=True).
      Predictions must be clearly labelled as model estimates on synthetic historical data.
"""

import os
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
SURPLUS_CSV = DATA_DIR / "historical_surplus.csv"
MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
SURPLUS_MODEL_PATH = MODEL_DIR / "surplus_rf_model.pkl"
SURPLUS_META_PATH = MODEL_DIR / "surplus_rf_meta.pkl"

# Day-name to integer mapping (consistent with the CSV)
DAY_ORDER = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def _build_features(df: pd.DataFrame,
                    org_enc: LabelEncoder,
                    cat_enc: LabelEncoder,
                    is_training: bool = True) -> pd.DataFrame:
    """
    Build the full feature matrix from the raw DataFrame.

    Features (no leakage — all derived from information available before prediction):
      - day_of_week_num  : 0=Mon ... 6=Sun
      - day_of_month     : 1-31
      - month            : 1-12
      - is_event_day     : 0/1 binary (event / peak indicator)
      - is_weekend       : 0/1 binary
      - org_encoded      : label-encoded organisation ID
      - cat_encoded      : label-encoded category
      - rolling_7d_mean  : per-(org, category) 7-day rolling mean of past quantities
      - rolling_7d_std   : per-(org, category) 7-day rolling std  of past quantities
      - lag_7            : quantity 7 days prior for same (org, category)

    Rolling & lag features look BACKWARD only, preventing data leakage into the future.
    During inference unknown organisations/categories are mapped to -1 (unseen).
    """
    feat = df.copy()

    # Temporal features
    feat["date"] = pd.to_datetime(feat["date"])
    feat["day_of_week_num"] = feat["day_of_week"].map(DAY_ORDER).fillna(0).astype(int)
    feat["day_of_month"] = feat["date"].dt.day
    feat["month"] = feat["date"].dt.month

    # Boolean to int
    feat["is_event_day"] = feat["is_event_day"].astype(int)
    feat["is_weekend"] = feat["is_weekend"].astype(int)

    # Encode categorical columns
    if is_training:
        org_enc.fit(feat["organization_id"].astype(str))
        cat_enc.fit(feat["category"].astype(str))
    feat["org_encoded"] = feat["organization_id"].astype(str).map(
        lambda x: int(org_enc.transform([x])[0]) if x in org_enc.classes_ else -1
    )
    feat["cat_encoded"] = feat["category"].astype(str).map(
        lambda x: int(cat_enc.transform([x])[0]) if x in cat_enc.classes_ else -1
    )

    # Sort so rolling/lag calculations are time-ordered per group
    feat = feat.sort_values(["organization_id", "category", "date"]).reset_index(drop=True)

    # Lag and rolling features per (org, category) — shift(1) avoids current-day leakage
    grp = feat.groupby(["organization_id", "category"])["quantity"]
    feat["lag_7"]           = grp.transform(lambda s: s.shift(7))
    feat["rolling_7d_mean"] = grp.transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
    feat["rolling_7d_std"]  = grp.transform(lambda s: s.shift(1).rolling(7, min_periods=1).std().fillna(0))

    return feat


FEATURE_COLS = [
    "day_of_week_num", "day_of_month", "month",
    "is_event_day", "is_weekend",
    "org_encoded", "cat_encoded",
    "rolling_7d_mean", "rolling_7d_std", "lag_7",
]
TARGET_COL = "quantity"


# ---------------------------------------------------------------------------
# SurplusPredictor class
# ---------------------------------------------------------------------------
class SurplusPredictor:
    """
    Explainable ML predictor for resource surplus quantities.

    Uses a RandomForestRegressor trained on synthetic historical surplus data
    with a strict time-based train/validation split to avoid data leakage.

    All predictions are estimates derived from SYNTHETIC historical data.
    They are NOT real-world forecasts.
    """

    MODEL_VERSION = "3.2.0"

    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.org_enc = LabelEncoder()
        self.cat_enc = LabelEncoder()
        self.is_trained = False
        self.metrics: Dict[str, float] = {}
        self.train_date_min: Optional[str] = None
        self.train_date_max: Optional[str] = None
        self.val_date_min: Optional[str] = None
        self.val_date_max: Optional[str] = None
        self.train_rows: int = 0
        self.val_rows: int = 0
        self.known_orgs: List[str] = []
        self.known_cats: List[str] = []

        # Attempt to load persisted model; train fresh if not found
        if not self._load():
            logger.info("No persisted surplus model found — training now.")
            self.train()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _save(self) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(SURPLUS_MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        meta = {
            "org_enc": self.org_enc,
            "cat_enc": self.cat_enc,
            "metrics": self.metrics,
            "train_date_min": self.train_date_min,
            "train_date_max": self.train_date_max,
            "val_date_min": self.val_date_min,
            "val_date_max": self.val_date_max,
            "train_rows": self.train_rows,
            "val_rows": self.val_rows,
            "known_orgs": self.known_orgs,
            "known_cats": self.known_cats,
        }
        with open(SURPLUS_META_PATH, "wb") as f:
            pickle.dump(meta, f)
        logger.info("Surplus model saved to %s", SURPLUS_MODEL_PATH)

    def _load(self) -> bool:
        if SURPLUS_MODEL_PATH.exists() and SURPLUS_META_PATH.exists():
            try:
                with open(SURPLUS_MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(SURPLUS_META_PATH, "rb") as f:
                    meta = pickle.load(f)
                self.org_enc = meta["org_enc"]
                self.cat_enc = meta["cat_enc"]
                self.metrics = meta["metrics"]
                self.train_date_min = meta["train_date_min"]
                self.train_date_max = meta["train_date_max"]
                self.val_date_min = meta["val_date_min"]
                self.val_date_max = meta["val_date_max"]
                self.train_rows = meta["train_rows"]
                self.val_rows = meta["val_rows"]
                self.known_orgs = meta["known_orgs"]
                self.known_cats = meta["known_cats"]
                self.is_trained = True
                logger.info("Surplus model loaded from disk (MAE=%.2f, RMSE=%.2f)",
                            self.metrics.get("mae", 0), self.metrics.get("rmse", 0))
                return True
            except Exception as e:
                logger.warning("Failed to load surplus model: %s — retraining.", e)
        return False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def train(self) -> Dict[str, Any]:
        """
        Load historical surplus data, engineer features, apply time-based
        train/validation split, train RandomForestRegressor, evaluate, and persist.

        Returns a summary dict with metrics and split information.
        """
        # --- Load ---
        if not SURPLUS_CSV.exists():
            raise FileNotFoundError(f"Historical surplus CSV not found: {SURPLUS_CSV}")

        df = pd.read_csv(SURPLUS_CSV)
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["quantity", "organization_id", "category"])

        # --- Feature engineering (fits encoders on full dataset) ---
        feat = _build_features(df, self.org_enc, self.cat_enc, is_training=True)

        # Drop rows where lag/rolling features are NaN (insufficient history)
        feat = feat.dropna(subset=FEATURE_COLS).reset_index(drop=True)

        self.known_orgs = list(self.org_enc.classes_)
        self.known_cats = list(self.cat_enc.classes_)

        # --- Time-based split (75 % train / 25 % validation) ---
        # Sort by date, never shuffle — preserves temporal ordering
        feat = feat.sort_values("date").reset_index(drop=True)
        split_idx = int(len(feat) * 0.75)
        train_df = feat.iloc[:split_idx]
        val_df   = feat.iloc[split_idx:]

        self.train_rows = len(train_df)
        self.val_rows   = len(val_df)
        self.train_date_min = str(train_df["date"].min().date())
        self.train_date_max = str(train_df["date"].max().date())
        self.val_date_min   = str(val_df["date"].min().date())
        self.val_date_max   = str(val_df["date"].max().date())

        X_train = train_df[FEATURE_COLS].fillna(0)
        y_train = train_df[TARGET_COL]
        X_val   = val_df[FEATURE_COLS].fillna(0)
        y_val   = val_df[TARGET_COL]

        # --- Train ---
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        # --- Evaluate on validation set ---
        y_pred = self.model.predict(X_val)
        mae  = float(mean_absolute_error(y_val, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_val, y_pred)))
        self.metrics = {"mae": round(mae, 4), "rmse": round(rmse, 4)}
        self.is_trained = True

        logger.info(
            "Surplus model trained | train=%d rows | val=%d rows | MAE=%.4f | RMSE=%.4f",
            self.train_rows, self.val_rows, mae, rmse,
        )

        self._save()
        return self._summary()

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        organization_id: str,
        category: str,
        target_date: str,
        is_event_day: bool = False,
    ) -> Dict[str, Any]:
        """
        Predict surplus quantity (kg) for a given org/category/date.

        Returns a dict with predicted_quantity (float), model metadata, and a
        synthetic-data disclaimer. Lag/rolling features default to the historical
        group mean when no live data is available for the target row.

        SYNTHETIC DATA — prediction is a model estimate only.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Surplus predictor is not trained yet.")

        target_dt = pd.Timestamp(target_date)

        # Build a single-row feature vector
        org_enc_val = (
            int(self.org_enc.transform([organization_id])[0])
            if organization_id in self.org_enc.classes_ else -1
        )
        cat_enc_val = (
            int(self.cat_enc.transform([category])[0])
            if category in self.cat_enc.classes_ else -1
        )

        # Load historical data to derive lag/rolling defaults for this org/cat
        df = pd.read_csv(SURPLUS_CSV, parse_dates=["date"])
        grp = df[(df["organization_id"] == organization_id) & (df["category"] == category)]
        grp = grp[grp["date"] < target_dt].sort_values("date")

        if len(grp) >= 7:
            lag_7 = float(grp["quantity"].iloc[-7])
            roll_mean = float(grp["quantity"].tail(7).mean())
            roll_std  = float(grp["quantity"].tail(7).std(ddof=0))
        elif len(grp) > 0:
            lag_7 = float(grp["quantity"].mean())
            roll_mean = float(grp["quantity"].mean())
            roll_std  = float(grp["quantity"].std(ddof=0) if len(grp) > 1 else 0.0)
        else:
            # Completely unknown org/cat — use global mean as fallback
            global_df = pd.read_csv(SURPLUS_CSV)
            lag_7 = float(global_df["quantity"].mean())
            roll_mean = lag_7
            roll_std  = float(global_df["quantity"].std())

        dow_name = target_dt.strftime("%A")
        row = {
            "day_of_week_num": DAY_ORDER.get(dow_name, 0),
            "day_of_month":    target_dt.day,
            "month":           target_dt.month,
            "is_event_day":    int(is_event_day),
            "is_weekend":      int(target_dt.weekday() >= 5),
            "org_encoded":     org_enc_val,
            "cat_encoded":     cat_enc_val,
            "rolling_7d_mean": roll_mean,
            "rolling_7d_std":  roll_std,
            "lag_7":           lag_7,
        }

        X = pd.DataFrame([row])[FEATURE_COLS]
        pred = float(self.model.predict(X)[0])
        pred = max(0.0, round(pred, 2))  # Quantity cannot be negative

        return {
            "organization_id":     organization_id,
            "category":            category,
            "target_date":         target_date,
            "is_event_day":        is_event_day,
            "predicted_quantity_kg": pred,
            "model":               f"RandomForestRegressor v{self.MODEL_VERSION}",
            "prediction_type":     "surplus",
            "data_disclaimer":     (
                "MODEL PREDICTION based on SYNTHETIC historical data (2025). "
                "Not a real-world forecast."
            ),
            "metrics": self.metrics,
        }

    # ------------------------------------------------------------------
    # Batch forecast
    # ------------------------------------------------------------------
    def forecast(
        self,
        organization_id: str,
        category: str,
        start_date: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Return day-by-day surplus predictions for `days` consecutive dates."""
        results = []
        base = pd.Timestamp(start_date)
        for i in range(days):
            date_str = str((base + pd.Timedelta(days=i)).date())
            results.append(self.predict(organization_id, category, date_str))
        return results

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------
    def _summary(self) -> Dict[str, Any]:
        return {
            "model_version":    self.MODEL_VERSION,
            "model_type":       "RandomForestRegressor",
            "features":         FEATURE_COLS,
            "train_date_range": (self.train_date_min, self.train_date_max),
            "val_date_range":   (self.val_date_min,   self.val_date_max),
            "train_rows":       self.train_rows,
            "val_rows":         self.val_rows,
            "metrics":          self.metrics,
            "known_orgs":       self.known_orgs,
            "known_cats":       self.known_cats,
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata (version, metrics, feature list, date ranges)."""
        if not self.is_trained:
            return {"status": "not_trained"}
        return self._summary()


# ---------------------------------------------------------------------------
# Module-level singleton — loaded/trained once at import time
# ---------------------------------------------------------------------------
surplus_predictor = SurplusPredictor()
