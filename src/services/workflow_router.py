"""
Workflow Router.

This module provides intelligent routing to select the appropriate workflow
based on query keywords and document characteristics.
"""

import logging
from typing import Optional

from src.workflows.workflow_types import WorkflowType

logger = logging.getLogger(__name__)


def get_workflow_type(
    query: str, explicit_workflow: Optional[str] = None
) -> WorkflowType:
    """Determine the appropriate workflow based on query keywords.

    The routing logic follows a priority order from most specific to least specific:

    1. TEXT_EXTRACTION - For simple text extraction without AI
    2. AZURE_DOCUMENT_INTELLIGENCE - For documents with complex tables/forms
    3. OCR_WITH_IMAGES - For scanned documents with images/charts
    4. GEMINI - For high-quality extraction with Google Gemini
    5. MISTRAL - Default fallback for general-purpose extraction

    Args:
        query: User query string to analyze for keywords
        explicit_workflow: Optional explicit workflow name (overrides keyword detection)

    Returns:
        WorkflowType enum value

    Raises:
        ValueError: If explicit_workflow is invalid

    Examples:
        >>> get_workflow_type("extract all tables with azure di")
        WorkflowType.AZURE_DOCUMENT_INTELLIGENCE

        >>> get_workflow_type("use gemini for high quality extraction")
        WorkflowType.GEMINI

        >>> get_workflow_type("extract text from scanned document")
        WorkflowType.OCR_WITH_IMAGES

        >>> get_workflow_type("extract data")
        WorkflowType.MISTRAL  # default
    """
    # If explicit workflow specified, use that
    if explicit_workflow:
        try:
            workflow_type = WorkflowType.from_string(explicit_workflow)
            logger.info(f"Using explicit workflow: {workflow_type.value}")
            return workflow_type
        except ValueError as e:
            logger.error(f"Invalid explicit workflow: {explicit_workflow}")
            raise ValueError(
                f"Invalid workflow type: {explicit_workflow}. "
                f"Valid options: {[wf.value for wf in WorkflowType]}"
            )

    # Analyze query for keywords
    query_lower = query.lower() if query else ""

    # Priority 1: TEXT_EXTRACTION (no AI)
    text_extraction_keywords = [
        "text extraction",
        "text only",
        "pdfplumber",
        "no ai",
        "raw text",
        "simple extraction",
        "plain text",
    ]
    if any(keyword in query_lower for keyword in text_extraction_keywords):
        logger.info("Routing to TEXT_EXTRACTION workflow (keyword match)")
        return WorkflowType.TEXT_EXTRACTION

    # Priority 2: AZURE_DOCUMENT_INTELLIGENCE (tables/forms)
    azure_di_keywords = [
        "azure di",
        "azure document intelligence",
        "document intelligence",
        "smart tables",
        "table extraction",
        "form",
        "invoice",
        "structured document",
        "layout",
    ]
    if any(keyword in query_lower for keyword in azure_di_keywords):
        logger.info("Routing to AZURE_DOCUMENT_INTELLIGENCE workflow (keyword match)")
        return WorkflowType.AZURE_DOCUMENT_INTELLIGENCE

    # Priority 3: OCR_WITH_IMAGES (scanned docs/images)
    ocr_keywords = [
        "ocr",
        "images",
        "charts",
        "diagrams",
        "scanned",
        "scan",
        "handwritten",
        "visual content",
        "image extraction",
    ]
    if any(keyword in query_lower for keyword in ocr_keywords):
        logger.info("Routing to OCR_WITH_IMAGES workflow (keyword match)")
        return WorkflowType.OCR_WITH_IMAGES

    # Priority 4: GEMINI (high quality)
    gemini_keywords = [
        "gemini",
        "google",
        "high quality",
        "best quality",
        "maximum quality",
    ]
    if any(keyword in query_lower for keyword in gemini_keywords):
        logger.info("Routing to GEMINI workflow (keyword match)")
        return WorkflowType.GEMINI

    # Priority 5: MISTRAL (default)
    logger.info("Routing to MISTRAL workflow (default)")
    return WorkflowType.MISTRAL


def get_workflow_description(workflow_type: WorkflowType) -> str:
    """Get a human-readable description of a workflow.

    Args:
        workflow_type: The workflow type to describe

    Returns:
        String description of the workflow
    """
    descriptions = {
        WorkflowType.MISTRAL: (
            "General-purpose extraction using Mistral AI. "
            "Best for general documents with a good balance of speed, cost, and quality."
        ),
        WorkflowType.TEXT_EXTRACTION: (
            "Fast text extraction using pdfplumber without AI. "
            "Best for simple text-based PDFs where AI enhancement is not needed."
        ),
        WorkflowType.AZURE_DOCUMENT_INTELLIGENCE: (
            "Intelligent extraction using Azure Document Intelligence. "
            "Best for documents with complex tables, forms, and structured layouts."
        ),
        WorkflowType.OCR_WITH_IMAGES: (
            "OCR extraction with image processing using OpenAI Vision. "
            "Best for scanned documents, charts, diagrams, and images with text."
        ),
        WorkflowType.GEMINI: (
            "High-quality extraction using Google Gemini. "
            "Best for when extraction quality is the top priority."
        ),
    }

    return descriptions.get(workflow_type, f"Unknown workflow: {workflow_type.value}")


def list_available_workflows() -> dict:
    """List all available workflows with their descriptions.

    Returns:
        Dictionary mapping workflow names to descriptions
    """
    return {
        workflow_type.value: get_workflow_description(workflow_type)
        for workflow_type in WorkflowType
    }
