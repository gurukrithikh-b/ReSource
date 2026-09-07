"""
Prediction Schemas — Phase 3.2
==============================
Pydantic request/response models for the ML prediction endpoints.
All predictions are based on SYNTHETIC historical data and are clearly
identified as model estimates, not real-world forecasts.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Request body for a single surplus or demand prediction."""
    organization_id: str = Field(
        ...,
        description="Organisation ID (e.g. 'hist-sup-001' for surplus, 'hist-rec-001' for demand)",
        examples=["hist-sup-001"],
    )
    category: str = Field(
        ...,
        description="Resource category (e.g. 'Cooked Meals', 'Fresh Produce', 'Bakery Items')",
        examples=["Cooked Meals"],
    )
    target_date: str = Field(
        ...,
        description="Target date in YYYY-MM-DD format",
        examples=["2026-01-15"],
    )
    is_event_day: bool = Field(
        default=False,
        description="Whether the target date is an event/peak day",
    )


class ForecastRequest(BaseModel):
    """Request body for a multi-day forecast."""
    organization_id: str = Field(..., description="Organisation ID")
    category: str = Field(..., description="Resource category")
    start_date: str = Field(..., description="First date of the forecast window (YYYY-MM-DD)")
    days: int = Field(default=7, ge=1, le=30, description="Number of days to forecast (1–30)")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ModelMetrics(BaseModel):
    """Validation-set evaluation metrics for a trained ML model."""
    mae: float = Field(..., description="Mean Absolute Error on validation set (kg)")
    rmse: float = Field(..., description="Root Mean Squared Error on validation set (kg)")


class PredictionResponse(BaseModel):
    """Single-point prediction response (surplus or demand)."""
    organization_id: str
    category: str
    target_date: str
    is_event_day: bool
    predicted_quantity_kg: float = Field(
        ...,
        description="Predicted resource quantity in kg",
    )
    model: str = Field(..., description="Model identifier and version")
    prediction_type: str = Field(..., description="'surplus' or 'demand'")
    data_disclaimer: str = Field(
        ...,
        description="Disclaimer that this is a model estimate on synthetic data",
    )
    metrics: ModelMetrics


class ForecastResponse(BaseModel):
    """Multi-day forecast response."""
    organization_id: str
    category: str
    start_date: str
    days: int
    prediction_type: str
    forecasts: List[PredictionResponse]
    data_disclaimer: str = (
        "MODEL PREDICTION based on SYNTHETIC historical data (2025). "
        "Not a real-world forecast."
    )


class ModelMetadataResponse(BaseModel):
    """Model metadata: version, features, date ranges, and validation metrics."""
    model_version: str
    model_type: str
    prediction_type: str
    features: List[str]
    train_date_range: Tuple[str, str]
    val_date_range: Tuple[str, str]
    train_rows: int
    val_rows: int
    metrics: ModelMetrics
    known_orgs: List[str]
    known_cats: List[str]
    data_source: str = "synthetic — historical_surplus.csv / historical_demand.csv (2025)"
    data_disclaimer: str = (
        "All training data is SYNTHETIC (is_simulated=True). "
        "Metrics and predictions reflect patterns in synthetic data only."
    )


class CombinedMetricsResponse(BaseModel):
    """Evaluation metrics for both surplus and demand models."""
    surplus: ModelMetadataResponse
    demand: ModelMetadataResponse
