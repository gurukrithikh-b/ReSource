from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Test database connectivity
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "database": db_status,
        "database_url": settings.DATABASE_URL.split("://")[0] + "://...",
        "modules": {
            "ai_nlp": "ready (stub)",
            "ml_prediction": "ready (stub)",
            "optimization_ortools": "ready (stub)",
            "impact_engine": "ready (stub)"
        }
    }
