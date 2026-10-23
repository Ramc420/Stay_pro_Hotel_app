import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "StayNest Pro – Hotel, Resort & Room Booking Management"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = ""
    
    # Database
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "SQLALCHEMY_DATABASE_URL", 
        "mysql+pymysql://root:Ramc%40123@localhost/hotel_resort"
    )
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "staynest-pro-secure-jwt-secret-key-32charslong!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_DOC_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "docx"]
    
    # Stripe (Test Mode)
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "sk_test_staynest_dummy_stripe_key")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_staynest_test_secret")
    
    # External AI Providers (Optional, graceful fallback enabled)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()
