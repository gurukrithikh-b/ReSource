from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.demand import UrgencyLevel, DemandStatus
from app.schemas.organization import OrganizationResponse

class DemandListingBase(BaseModel):
    receiver_id: str
    category_id: str
    title: str
    raw_nlp_text: Optional[str] = None
    requested_quantity: float
    unit: str = "kg"
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    storage_capacity: str = "AMBIENT"
    required_by: Optional[datetime] = None
    is_simulated: bool = True

class DemandListingCreate(BaseModel):
    receiver_id: Optional[str] = None
    category_id: Optional[str] = None
    title: Optional[str] = None
    raw_nlp_text: Optional[str] = None
    requested_quantity: Optional[float] = None
    unit: Optional[str] = None
    urgency_level: Optional[UrgencyLevel] = None
    storage_capacity: Optional[str] = None
    required_by: Optional[datetime] = None
    is_simulated: bool = True

class DemandListingResponse(DemandListingBase):
    id: str
    fulfilled_quantity: float
    status: DemandStatus
    created_at: datetime
    receiver: Optional[OrganizationResponse] = None

    class Config:
        from_attributes = True
