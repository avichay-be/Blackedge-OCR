"""
API request and response models.

This module defines Pydantic models for API endpoints,
including request bodies, response formats, and health checks.

Example:
    from src.models.api_models import ExtractionResponse

    response = ExtractionResponse(
        status="success",
        content="Extracted text...",
        metadata={"pages": 10}
    )
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ExtractionRequest(BaseModel):
    """Request model for PDF extraction endpoints."""

    query: str = Field("", description="Query/prompt to guide extraction")
    enable_validation: Optional[bool] = Field(None, description="Override global validation setting")
    workflow_type: Optional[str] = Field(None, description="Specific workflow to use")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "extract all tables and financial data",
                "enable_validation": True,
                "workflow_type": "azure_di"
            }
        }


class ExtractionResponse(BaseModel):
    """Response model for successful PDF extraction."""

    status: str = Field("success", description="Response status")
    content: str = Field(..., description="Extracted content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extraction metadata")
    validation_report: Optional[Dict[str, Any]] = Field(None, description="Validation report if enabled")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "content": "# Extracted Document\n\nContent here...",
                "metadata": {
                    "workflow": "mistral",
                    "pages": 10,
                    "file_size_mb": 2.5
                },
                "validation_report": None,
                "processing_time_seconds": 45.2
            }
        }


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    status: str = Field("error", description="Response status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": "Extraction failed",
                "detail": "PDF file is corrupted",
                "timestamp": "2026-01-09T12:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field("1.0.0", description="API version")
    environment: Optional[str] = Field(None, description="Environment name")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-01-09T12:00:00Z",
                "version": "1.0.0",
                "environment": "production"
            }
        }


class DetailedHealthResponse(HealthResponse):
    """Detailed health check with component status."""

    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Health status of individual components"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-01-09T12:00:00Z",
                "version": "1.0.0",
                "environment": "production",
                "components": {
                    "mistral_client": {"status": "healthy", "latency_ms": 150},
                    "openai_client": {"status": "healthy", "latency_ms": 200},
                    "gemini_client": {"status": "healthy", "latency_ms": 180}
                }
            }
        }
