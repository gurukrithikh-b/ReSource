from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

class ImpactLog(Base):
    __tablename__ = "impact_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    allocation_id = Column(String, ForeignKey("allocations.id"), nullable=True)
    
    resource_recovered_kg = Column(Float, nullable=False)
    demand_fulfilled_kg = Column(Float, nullable=False, default=0.0)
    meals_provided_estimate = Column(Float, nullable=True)
    co2_avoided_kg = Column(Float, nullable=True)
    water_saved_liters = Column(Float, nullable=True)
    
    category = Column(String, nullable=True)
    supplier_id = Column(String, nullable=True)
    supplier_name = Column(String, nullable=True)
    receiver_id = Column(String, nullable=True)
    receiver_name = Column(String, nullable=True)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    allocation = relationship("Allocation", back_populates="impact_logs")


def ensure_impact_table_schema(db_engine):
    """Ensure SQLite impact_logs table has all Phase 5 columns."""
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(db_engine)
        if "impact_logs" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("impact_logs")}
            needed_cols = {
                "demand_fulfilled_kg": "FLOAT DEFAULT 0.0",
                "category": "VARCHAR",
                "supplier_id": "VARCHAR",
                "supplier_name": "VARCHAR",
                "receiver_id": "VARCHAR",
                "receiver_name": "VARCHAR",
            }
            with db_engine.connect() as conn:
                for col_name, col_type in needed_cols.items():
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE impact_logs ADD COLUMN {col_name} {col_type}"))
                conn.commit()
    except Exception:
        pass


