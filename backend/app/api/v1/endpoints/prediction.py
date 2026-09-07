"""
Prediction API Endpoints — Phase 3.2: Predictive Supply & Demand Engine
=======================================================================
All predictions are derived from SYNTHETIC historical data (Jan–Dec 2025).
They are clearly identified as model estimates, NOT real-world forecasts.

Endpoints:
  POST /predictions/surplus          — single surplus prediction
  POST /predictions/demand           — single demand prediction
  POST /predictions/surplus/forecast — multi-day surplus forecast
  POST /predictions/demand/forecast  — multi-day demand forecast
  GET  /predictions/metrics          — evaluation metrics for both models
  GET  /predictions/metrics/surplus  — surplus model metadata
  GET  /predictions/metrics/demand   — demand model metadata
  POST /predictions/retrain          — force model retraining from source CSVs
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from app.ml.surplus_predictor import surplus_predictor
from app.ml.demand_predictor import demand_predictor
from app.schemas.prediction import (
    PredictionRequest,
    ForecastRequest,
    PredictionResponse,
    ForecastResponse,
    ModelMetadataResponse,
    CombinedMetricsResponse,
    ModelMetrics,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: build ModelMetadataResponse from a predictor instance
# ---------------------------------------------------------------------------
def _surplus_metadata() -> ModelMetadataResponse:
    meta = surplus_predictor.get_metadata()
    return ModelMetadataResponse(
        model_version=meta["model_version"],
        model_type=meta["model_type"],
        prediction_type="surplus",
        features=meta["features"],
        train_date_range=tuple(meta["train_date_range"]),
        val_date_range=tuple(meta["val_date_range"]),
        train_rows=meta["train_rows"],
        val_rows=meta["val_rows"],
        metrics=ModelMetrics(**meta["metrics"]),
        known_orgs=meta["known_orgs"],
        known_cats=meta["known_cats"],
    )


def _demand_metadata() -> ModelMetadataResponse:
    meta = demand_predictor.get_metadata()
    return ModelMetadataResponse(
        model_version=meta["model_version"],
        model_type=meta["model_type"],
        prediction_type="demand",
        features=meta["features"],
        train_date_range=tuple(meta["train_date_range"]),
        val_date_range=tuple(meta["val_date_range"]),
        train_rows=meta["train_rows"],
        val_rows=meta["val_rows"],
        metrics=ModelMetrics(**meta["metrics"]),
        known_orgs=meta["known_orgs"],
        known_cats=meta["known_cats"],
    )


# ---------------------------------------------------------------------------
# Single-point predictions
# ---------------------------------------------------------------------------

@router.post(
    "/surplus",
    response_model=PredictionResponse,
    summary="Predict surplus quantity",
    description=(
        "Predict the expected surplus resource quantity (kg) for a given "
        "organisation, category, and date. "
        "**MODEL PREDICTION — based on SYNTHETIC historical data. Not a real-world forecast.**"
    ),
)
def predict_surplus(request: PredictionRequest) -> PredictionResponse:
    """
    Return a surplus quantity prediction from the trained RandomForestRegressor.

    - `organization_id`: supplier org ID (e.g. 'hist-sup-001')
    - `category`: resource category (e.g. 'Cooked Meals')
    - `target_date`: YYYY-MM-DD
    - `is_event_day`: optional peak/event flag
    """
    try:
        result = surplus_predictor.predict(
            organization_id=request.organization_id,
            category=request.category,
            target_date=request.target_date,
            is_event_day=request.is_event_day,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Surplus prediction failed: {str(e)}",
        )
    return PredictionResponse(
        organization_id=result["organization_id"],
        category=result["category"],
        target_date=result["target_date"],
        is_event_day=result["is_event_day"],
        predicted_quantity_kg=result["predicted_quantity_kg"],
        model=result["model"],
        prediction_type=result["prediction_type"],
        data_disclaimer=result["data_disclaimer"],
        metrics=ModelMetrics(**result["metrics"]),
    )


@router.post(
    "/demand",
    response_model=PredictionResponse,
    summary="Predict community demand quantity",
    description=(
        "Predict the expected resource demand (kg) for a given receiver "
        "organisation, category, and date. "
        "**MODEL PREDICTION — based on SYNTHETIC historical data. Not a real-world forecast.**"
    ),
)
def predict_demand(request: PredictionRequest) -> PredictionResponse:
    """
    Return a demand quantity prediction from the trained RandomForestRegressor.

    - `organization_id`: receiver org ID (e.g. 'hist-rec-001')
    - `category`: resource category (e.g. 'Cooked Meals')
    - `target_date`: YYYY-MM-DD
    - `is_event_day`: optional peak/event flag
    """
    try:
        result = demand_predictor.predict(
            organization_id=request.organization_id,
            category=request.category,
            target_date=request.target_date,
            is_event_day=request.is_event_day,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand prediction failed: {str(e)}",
        )
    return PredictionResponse(
        organization_id=result["organization_id"],
        category=result["category"],
        target_date=result["target_date"],
        is_event_day=result["is_event_day"],
        predicted_quantity_kg=result["predicted_quantity_kg"],
        model=result["model"],
        prediction_type=result["prediction_type"],
        data_disclaimer=result["data_disclaimer"],
        metrics=ModelMetrics(**result["metrics"]),
    )


# ---------------------------------------------------------------------------
# Multi-day forecasts
# ---------------------------------------------------------------------------

@router.post(
    "/surplus/forecast",
    response_model=ForecastResponse,
    summary="Multi-day surplus forecast",
    description=(
        "Forecast surplus resource quantities for a window of consecutive dates. "
        "**MODEL PREDICTION — SYNTHETIC data only.**"
    ),
)
def forecast_surplus(request: ForecastRequest) -> ForecastResponse:
    """Return a day-by-day surplus forecast for up to 30 consecutive dates."""
    try:
        results = surplus_predictor.forecast(
            organization_id=request.organization_id,
            category=request.category,
            start_date=request.start_date,
            days=request.days,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Surplus forecast failed: {str(e)}",
        )
    forecasts = [
        PredictionResponse(
            organization_id=r["organization_id"],
            category=r["category"],
            target_date=r["target_date"],
            is_event_day=r["is_event_day"],
            predicted_quantity_kg=r["predicted_quantity_kg"],
            model=r["model"],
            prediction_type=r["prediction_type"],
            data_disclaimer=r["data_disclaimer"],
            metrics=ModelMetrics(**r["metrics"]),
        )
        for r in results
    ]
    return ForecastResponse(
        organization_id=request.organization_id,
        category=request.category,
        start_date=request.start_date,
        days=request.days,
        prediction_type="surplus",
        forecasts=forecasts,
    )


@router.post(
    "/demand/forecast",
    response_model=ForecastResponse,
    summary="Multi-day demand forecast",
    description=(
        "Forecast community demand quantities for a window of consecutive dates. "
        "**MODEL PREDICTION — SYNTHETIC data only.**"
    ),
)
def forecast_demand(request: ForecastRequest) -> ForecastResponse:
    """Return a day-by-day demand forecast for up to 30 consecutive dates."""
    try:
        results = demand_predictor.forecast(
            organization_id=request.organization_id,
            category=request.category,
            start_date=request.start_date,
            days=request.days,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand forecast failed: {str(e)}",
        )
    forecasts = [
        PredictionResponse(
            organization_id=r["organization_id"],
            category=r["category"],
            target_date=r["target_date"],
            is_event_day=r["is_event_day"],
            predicted_quantity_kg=r["predicted_quantity_kg"],
            model=r["model"],
            prediction_type=r["prediction_type"],
            data_disclaimer=r["data_disclaimer"],
            metrics=ModelMetrics(**r["metrics"]),
        )
        for r in results
    ]
    return ForecastResponse(
        organization_id=request.organization_id,
        category=request.category,
        start_date=request.start_date,
        days=request.days,
        prediction_type="demand",
        forecasts=forecasts,
    )


# ---------------------------------------------------------------------------
# Model metadata & evaluation metrics
# ---------------------------------------------------------------------------

@router.get(
    "/metrics",
    response_model=CombinedMetricsResponse,
    summary="Evaluation metrics — both models",
    description=(
        "Return MAE / RMSE and metadata for both the surplus and demand models. "
        "Metrics are computed on the held-out validation set (time-based split). "
        "**All data is SYNTHETIC.**"
    ),
)
def get_combined_metrics() -> CombinedMetricsResponse:
    """Return real validation-set MAE and RMSE for surplus and demand models."""
    if not surplus_predictor.is_trained:
        raise HTTPException(status_code=503, detail="Surplus model not ready.")
    if not demand_predictor.is_trained:
        raise HTTPException(status_code=503, detail="Demand model not ready.")
    return CombinedMetricsResponse(
        surplus=_surplus_metadata(),
        demand=_demand_metadata(),
    )


@router.get(
    "/metrics/surplus",
    response_model=ModelMetadataResponse,
    summary="Surplus model metadata",
    description="Return version, features, training date range, and validation metrics for the surplus model.",
)
def get_surplus_metrics() -> ModelMetadataResponse:
    """Surplus model metadata including real MAE / RMSE from the validation set."""
    if not surplus_predictor.is_trained:
        raise HTTPException(status_code=503, detail="Surplus model not ready.")
    return _surplus_metadata()


@router.get(
    "/metrics/demand",
    response_model=ModelMetadataResponse,
    summary="Demand model metadata",
    description="Return version, features, training date range, and validation metrics for the demand model.",
)
def get_demand_metrics() -> ModelMetadataResponse:
    """Demand model metadata including real MAE / RMSE from the validation set."""
    if not demand_predictor.is_trained:
        raise HTTPException(status_code=503, detail="Demand model not ready.")
    return _demand_metadata()


# ---------------------------------------------------------------------------
# Force retrain
# ---------------------------------------------------------------------------

@router.post(
    "/retrain",
    summary="Force model retraining",
    description=(
        "Delete cached model artifacts and retrain both surplus and demand models "
        "from source CSV files. Returns updated metrics. "
        "**Data is SYNTHETIC — for development/testing only.**"
    ),
)
def retrain_models() -> dict:
    """
    Force retraining of both ML models from the raw historical CSVs.
    Useful after updating the source data files.
    """
    try:
        surplus_summary = surplus_predictor.train()
        demand_summary  = demand_predictor.train()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retraining failed: {str(e)}",
        )
    return {
        "status": "retrained",
        "surplus": {
            "train_rows": surplus_summary["train_rows"],
            "val_rows":   surplus_summary["val_rows"],
            "metrics":    surplus_summary["metrics"],
            "train_date_range": surplus_summary["train_date_range"],
            "val_date_range":   surplus_summary["val_date_range"],
        },
        "demand": {
            "train_rows": demand_summary["train_rows"],
            "val_rows":   demand_summary["val_rows"],
            "metrics":    demand_summary["metrics"],
            "train_date_range": demand_summary["train_date_range"],
            "val_date_range":   demand_summary["val_date_range"],
        },
        "data_disclaimer": (
            "MODEL PREDICTION based on SYNTHETIC historical data (2025). "
            "Not a real-world forecast."
        ),
    }
