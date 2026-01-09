"""
Core configuration module.

This module provides the Settings class for loading and validating
application configuration from environment variables using Pydantic Settings.

Example:
    from src.core.config import settings

    api_key = settings.AZURE_API_KEY
    timeout = settings.REQUEST_TIMEOUT
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys - AI Providers
    AZURE_API_KEY: str = Field(..., description="Azure API key for Mistral/OpenAI")
    MISTRAL_API_URL: str = Field(..., description="Mistral API endpoint URL")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    GEMINI_API_KEY: Optional[str] = Field(None, description="Google Gemini API key")
    AZURE_DI_ENDPOINT: Optional[str] = Field(None, description="Azure Document Intelligence endpoint")
    AZURE_DI_KEY: Optional[str] = Field(None, description="Azure Document Intelligence API key")

    # Application Settings
    API_KEY: Optional[str] = Field(None, description="API key for authentication")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    ENVIRONMENT: str = Field("development", description="Environment (development/production)")

    # Validation Configuration
    ENABLE_CROSS_VALIDATION: bool = Field(False, description="Enable cross-validation with secondary AI")
    VALIDATION_SIMILARITY_THRESHOLD: float = Field(0.95, description="Similarity threshold for validation")
    VALIDATION_SIMILARITY_METHOD: str = Field("number_frequency", description="Similarity calculation method")

    # Processing Configuration
    DEFAULT_CHUNK_SIZE: int = Field(50, description="Default chunk size for processing (pages)")
    MAX_CONCURRENT_REQUESTS: int = Field(5, description="Maximum concurrent API requests")
    REQUEST_TIMEOUT: int = Field(120, description="Request timeout in seconds")

    # Server Configuration
    HOST: str = Field("0.0.0.0", description="Server host")
    PORT: int = Field(8000, description="Server port")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
