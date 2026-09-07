from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.allocation import AllocationStatus
from app.schemas.surplus import SurplusListingResponse
from app.schemas.demand import DemandListingResponse

class AllocationBase(BaseModel):
    surplus_id: str
    demand_id: str
    allocated_quantity: float
    match_score: float
    distance_km: Optional[float] = None
    estimated_transit_minutes: Optional[float] = None

class AllocationCreate(AllocationBase):
    pass

class AllocationResponse(AllocationBase):
    id: str
    status: AllocationStatus
    created_at: datetime
    surplus: Optional[SurplusListingResponse] = None
    demand: Optional[DemandListingResponse] = None

    class Config:
        from_attributes = True
