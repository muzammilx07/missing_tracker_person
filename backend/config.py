from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # JWT & Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_DAYS: int = 7
    
    # Cloudinary (optional)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Face Recognition Thresholds
    FACE_AUTO_THRESHOLD: float = 0.85  # High-confidence match
    FACE_REVIEW_THRESHOLD: float = 0.60  # Possible match threshold

    # Sighting persistence policy after matching
    STORE_MATCHED_SIGHTINGS: bool = True
    STORE_UNMATCHED_SIGHTINGS: bool = False
    
    # Nominatim (OpenStreetMap geocoding) - Free, no key needed
    NOMINATIM_USER_AGENT: str = "missing-tracker-app"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tracker.db"
    DIRECT_URL: Optional[str] = None  # Supabase direct URL for migrations


settings = Settings()
