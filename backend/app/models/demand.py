import enum
from sqlalchemy import Column, String, Float, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class UrgencyLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DemandStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"

class DemandListing(Base):
    __tablename__ = "demand_listings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    receiver_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    
    title = Column(String, nullable=False)
    raw_nlp_text = Column(Text, nullable=True) # Unstructured demand notes
    requested_quantity = Column(Float, nullable=False)
    fulfilled_quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String, nullable=False, default="kg")
    
    urgency_level = Column(Enum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM)
    storage_capacity = Column(String, nullable=False, default="AMBIENT")
    
    required_by = Column(DateTime, nullable=False)
    status = Column(Enum(DemandStatus), nullable=False, default=DemandStatus.OPEN)
    
    is_simulated = Column(Boolean, nullable=False, default=True) # Clearly marks mock/simulated data
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    receiver = relationship("Organization", back_populates="demand_listings")
    category = relationship("Category", back_populates="demand_listings")
    allocations = relationship("Allocation", back_populates="demand")
