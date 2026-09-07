from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.surplus import StorageCondition, SurplusStatus
from app.schemas.organization import OrganizationResponse

class SurplusListingBase(BaseModel):
    supplier_id: str
    category_id: str
    title: str
    raw_nlp_text: Optional[str] = None
    quantity: float
    unit: str = "kg"
    perishability_hours: float = 12.0
    storage_condition: StorageCondition = StorageCondition.AMBIENT
    available_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_simulated: bool = True

class SurplusListingCreate(BaseModel):
    supplier_id: Optional[str] = None
    category_id: Optional[str] = None
    title: Optional[str] = None
    raw_nlp_text: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    perishability_hours: Optional[float] = None
    storage_condition: Optional[StorageCondition] = None
    available_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_simulated: bool = True

class SurplusListingResponse(SurplusListingBase):
    id: str
    remaining_quantity: float
    status: SurplusStatus
    created_at: datetime
    supplier: Optional[OrganizationResponse] = None

    class Config:
        from_attributes = True
