import enum
from sqlalchemy import Column, String, Float, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class OrganizationType(str, enum.Enum):
    RESTAURANT = "RESTAURANT"
    HOTEL = "HOTEL"
    EVENT_VENUE = "EVENT_VENUE"
    INSTITUTION = "INSTITUTION"
    NGO = "NGO"
    FOOD_BANK = "FOOD_BANK"
    COMMUNITY_SHELTER = "COMMUNITY_SHELTER"

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    org_type = Column(Enum(OrganizationType), nullable=False)
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    surplus_listings = relationship("SurplusListing", back_populates="supplier")
    demand_listings = relationship("DemandListing", back_populates="receiver")
