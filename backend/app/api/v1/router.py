from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    organizations,
    surplus,
    demand,
    prediction,
    matching,
    optimization,
    impact,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health System"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(surplus.router, prefix="/surplus", tags=["Surplus Listings"])
api_router.include_router(demand.router, prefix="/demand", tags=["Demand Listings"])
api_router.include_router(prediction.router, prefix="/predictions", tags=["ML Predictions (Phase 3.2)"])
api_router.include_router(matching.router, prefix="/matching", tags=["Smart Matching (Phase 3.3)"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["Multi-Point Optimization (Phase 4.2)"])
api_router.include_router(impact.router, prefix="/impact", tags=["Sustainability Impact (Phase 5)"])



