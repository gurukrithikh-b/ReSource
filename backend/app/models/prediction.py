import enum
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey
from datetime import datetime
import uuid
from app.core.database import Base

class PredictionType(str, enum.Enum):
    SURPLUS_FORECAST = "SURPLUS_FORECAST"
    DEMAND_FORECAST = "DEMAND_FORECAST"

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    prediction_type = Column(Enum(PredictionType), nullable=False)
    
    target_date = Column(DateTime, nullable=False)
    predicted_quantity = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String, nullable=False, default="v0.1-stub")
    
    created_at = Column(DateTime, default=datetime.utcnow)
