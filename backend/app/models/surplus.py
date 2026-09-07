import enum
from sqlalchemy import Column, String, Float, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class StorageCondition(str, enum.Enum):
    AMBIENT = "AMBIENT"
    REFRIGERATED = "REFRIGERATED"
    FROZEN = "FROZEN"

class SurplusStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    MATCHED = "MATCHED"
    ALLOCATED = "ALLOCATED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

class SurplusListing(Base):
    __tablename__ = "surplus_listings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    
    title = Column(String, nullable=False)
    raw_nlp_text = Column(Text, nullable=True) # Unstructured natural language note submitted by supplier
    quantity = Column(Float, nullable=False)
    remaining_quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default="kg")
    
    perishability_hours = Column(Float, nullable=False) # Total shelf-life hours from post
    storage_condition = Column(Enum(StorageCondition), nullable=False, default=StorageCondition.AMBIENT)
    
    available_from = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(Enum(SurplusStatus), nullable=False, default=SurplusStatus.AVAILABLE)
    
    is_simulated = Column(Boolean, nullable=False, default=True) # Clearly marks mock/simulated data
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supplier = relationship("Organization", back_populates="surplus_listings")
    category = relationship("Category", back_populates="surplus_listings")
    allocations = relationship("Allocation", back_populates="surplus")
