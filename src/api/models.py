"""
API Models.

Pydantic models for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """Request model for extraction endpoint."""

    query: str = Field(
        default="",
        description="User query providing context for extraction",
        example="extract all tables and financial data",
    )
    enable_validation: Optional[bool] = Field(
        default=None,
        description="Enable cross-validation with secondary AI (overrides global setting)",
    )
    workflow: Optional[str] = Field(
        default=None,
        description="Explicit workflow to use (mistral, gemini, azure_di, ocr_images, text_extraction)",
        example="mistral",
    )


class Base64ExtractionRequest(ExtractionRequest):
    """Request model for base64 PDF extraction."""

    pdf_content: str = Field(..., description="Base64-encoded PDF file content")
    filename: Optional[str] = Field(
        default=None, description="Original filename (for logging)"
    )


class PageSection(BaseModel):
    """Model for individual page section."""

    page_number: int = Field(..., description="Page number")
    content: str = Field(..., description="Extracted content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Page-level metadata"
    )


class ExtractionResponse(BaseModel):
    """Response model for extraction endpoint."""

    status: str = Field(..., description="Response status (success/error)")
    content: str = Field(..., description="Complete extracted content")
    metadata: Dict[str, Any] = Field(..., description="Extraction metadata")
    validation_report: Optional[Dict[str, Any]] = Field(
        default=None, description="Validation report (if validation enabled)"
    )
    sections: Optional[List[PageSection]] = Field(
        default=None, description="Individual page sections"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "content": "Extracted text content from PDF...",
                "metadata": {
                    "workflow": "mistral",
                    "provider": "mistral",
                    "pages": 5,
                    "processing_time_seconds": 12.34,
                },
                "validation_report": {"similarity": 0.98},
                "sections": [
                    {
                        "page_number": 1,
                        "content": "Page 1 content...",
                        "metadata": {},
                    }
                ],
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error conditions."""

    status: str = Field(default="error", description="Response status")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error": "Invalid PDF file",
                "details": {"reason": "Missing PDF header"},
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="Application version")
    clients: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Status of AI clients"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "clients": {
                    "mistral": {"status": "ok", "model": "mistral-large"},
                    "openai": {"status": "ok", "model": "gpt-4"},
                },
            }
        }


class WorkflowListResponse(BaseModel):
    """Response model for listing available workflows."""

    workflows: Dict[str, str] = Field(
        ..., description="Available workflows with descriptions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "workflows": {
                    "mistral": "General-purpose extraction using Mistral AI",
                    "gemini": "High-quality extraction using Google Gemini",
                    "azure_di": "Best for complex tables and forms",
                    "ocr_images": "Best for scanned documents and images",
                    "text_extraction": "Fast extraction without AI",
                }
            }
        }
