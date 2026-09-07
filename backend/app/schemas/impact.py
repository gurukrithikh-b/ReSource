"""
Pydantic Schemas for Phase 5 — Sustainability Impact Intelligence API
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ImpactCalculateItem(BaseModel):
    allocation_id: Optional[str] = None
    surplus_id: Optional[str] = None
    demand_id: Optional[str] = None
    allocated_quantity: float = Field(..., description="Quantity allocated in kg")
    category_name: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    receiver_id: Optional[str] = None
    receiver_name: Optional[str] = None


class ImpactCalculateRequest(BaseModel):
    allocations: List[ImpactCalculateItem]


class ImpactRecordSchema(BaseModel):
    id: str
    allocation_id: Optional[str] = None
    resource_recovered_kg: float
    demand_fulfilled_kg: float
    meals_provided_estimate: Optional[float] = None
    co2_avoided_kg: Optional[float] = None
    category: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    receiver_id: Optional[str] = None
    receiver_name: Optional[str] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


class ImpactSummarySchema(BaseModel):
    total_resources_rescued_kg: float
    total_demand_fulfilled_kg: float
    total_meals_served: float
    total_co2_avoided_kg: float
    unique_community_partners: int
    total_successful_allocations: int
    data_source: str = "LIVE_OPTIMIZATION_IMPACT"
    message: str = "Sustainability impact calculated from optimized allocations"


class ImpactTrendItemSchema(BaseModel):
    date: str  # YYYY-MM-DD, YYYY-WW, or YYYY-MM
    resources_rescued_kg: float
    demand_fulfilled_kg: float
    co2_avoided_kg: float
    meals_served: float
    allocations_count: int


class ImpactCategoryGroupSchema(BaseModel):
    category: str
    resources_rescued_kg: float
    co2_avoided_kg: float
    meals_served: float
    allocations_count: int


class ImpactProviderGroupSchema(BaseModel):
    provider_name: str
    resources_rescued_kg: float
    co2_avoided_kg: float
    meals_served: float
    allocations_count: int


class ImpactPartnerGroupSchema(BaseModel):
    partner_name: str
    resources_rescued_kg: float
    demand_fulfilled_kg: float
    meals_served: float
    allocations_count: int
