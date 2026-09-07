from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.organization import OrganizationType

class OrganizationBase(BaseModel):
    name: str
    org_type: OrganizationType
    address: str
    latitude: float
    longitude: float
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_verified: bool = True

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
