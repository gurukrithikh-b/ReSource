from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ParseIntakeRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured natural language food surplus or demand description")

class ParsedIntakeResponse(BaseModel):
    raw_text: str
    resource_type: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    storage_condition: Optional[str] = None # REFRIGERATED, FROZEN, AMBIENT
    perishability_hours: Optional[float] = None
    expires_at: Optional[datetime] = None
    required_by: Optional[datetime] = None
    deadline_display: Optional[str] = None # e.g., "9:00 PM today"
    food_subtype: Optional[str] = None # e.g. vegetarian, vegan, bakery, produce
    urgency_level: Optional[str] = None # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float = Field(0.0, description="Rule-based deterministic extraction match confidence score between 0.0 and 1.0")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
