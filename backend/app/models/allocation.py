import enum
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class AllocationStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Allocation(Base):
    __tablename__ = "allocations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    surplus_id = Column(String, ForeignKey("surplus_listings.id"), nullable=False)
    demand_id = Column(String, ForeignKey("demand_listings.id"), nullable=False)
    
    allocated_quantity = Column(Float, nullable=False)
    match_score = Column(Float, nullable=False, default=0.0) # Transparent match score 0.0 - 1.0
    distance_km = Column(Float, nullable=True)
    estimated_transit_minutes = Column(Float, nullable=True)
    
    status = Column(Enum(AllocationStatus), nullable=False, default=AllocationStatus.PROPOSED)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    surplus = relationship("SurplusListing", back_populates="allocations")
    demand = relationship("DemandListing", back_populates="allocations")
    impact_logs = relationship("ImpactLog", back_populates="allocation")
