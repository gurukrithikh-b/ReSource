import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReSource"
    PROJECT_TAGLINE: str = "Predict. Match. Redistribute. Sustain."
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration: Zero-config SQLite fallback for local development, easily configured to PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./resource.db")
    
    # Secret Key & Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "resource-secret-key-change-in-production")
    
    class Config:
        case_sensitive = True

settings = Settings()
