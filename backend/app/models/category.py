from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True) # e.g. "Food Surplus", "Cooked Meals", "Raw Produce"
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    default_unit = Column(String, nullable=False, default="kg") # e.g., "kg", "portions", "units"

    # Relationships
    parent = relationship("Category", remote_side=[id])
    surplus_listings = relationship("SurplusListing", back_populates="category")
    demand_listings = relationship("DemandListing", back_populates="category")
