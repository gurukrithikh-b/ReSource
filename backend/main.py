from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import app.models  # Ensures all models are registered with Base

from app.models.impact import ensure_impact_table_schema

# Create database tables on startup
Base.metadata.create_all(bind=engine)
ensure_impact_table_schema(engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Predictive Circular Resource Intelligence Network API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https://.*\.onrender\.com|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.router import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "tagline": settings.PROJECT_TAGLINE,
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health"
    }
