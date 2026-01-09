"""
Workflow data models.

This module defines Pydantic models for workflow execution results,
extracted content sections, and validation results.

Example:
    from src.models.workflow_models import WorkflowResult

    result = WorkflowResult(
        content="Extracted text...",
        metadata={"workflow": "mistral", "pages": 10}
    )
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExtractedSection(BaseModel):
    """Represents content extracted from a single PDF page."""

    page_number: int = Field(..., description="Page number (1-indexed)")
    content: str = Field(..., description="Extracted text content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional page metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "page_number": 1,
                "content": "# Page 1\n\nThis is the extracted content...",
                "metadata": {"word_count": 150, "has_images": True}
            }
        }


class ValidationResult(BaseModel):
    """Result of content validation process."""

    content: str = Field(..., description="Validated content (may be from secondary extraction)")
    used_secondary: bool = Field(False, description="Whether secondary extraction was used")
    report: Dict[str, Any] = Field(default_factory=dict, description="Validation report details")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Validated extracted text...",
                "used_secondary": False,
                "report": {
                    "similarity": 0.98,
                    "problems_detected": []
                }
            }
        }


class WorkflowResult(BaseModel):
    """Complete result from workflow execution."""

    content: str = Field(..., description="Full extracted content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Workflow execution metadata")
    sections: Optional[List[ExtractedSection]] = Field(None, description="Individual page sections")
    validation_report: Optional[Dict[str, Any]] = Field(None, description="Validation report if enabled")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of extraction")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Full Document\n\nExtracted content from all pages...",
                "metadata": {
                    "workflow": "mistral",
                    "pages": 10,
                    "processing_time_seconds": 45.2
                },
                "sections": [
                    {
                        "page_number": 1,
                        "content": "Page 1 content...",
                        "metadata": {}
                    }
                ],
                "validation_report": None,
                "created_at": "2026-01-09T12:00:00Z"
            }
        }
