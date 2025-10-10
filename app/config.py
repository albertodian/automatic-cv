"""
Configuration settings for the FastAPI application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_TITLE: str = "Automatic CV Generator API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Generate optimized CVs tailored to job descriptions using AI"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False  # Set to False in production
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]  # Update with specific origins in production
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # LLM Settings
    DEFAULT_MODEL: str = "openai/gpt-4.1-mini"
    MAX_RETRIES: int = 2
    
    # File Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    OUTPUT_DIR: str = "output"
    TEMP_DIR: str = "output/temp"
    
    # Templates
    AVAILABLE_TEMPLATES: List[str] = ["tech", "business", "modern"]
    DEFAULT_TEMPLATE: str = "tech"
    
    # API Keys (loaded from environment)
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # This allows extra env vars like SUPABASE_URL without errors
    )


# Global settings instance
settings = Settings()
