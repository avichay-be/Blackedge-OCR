"""
Workflow Types Enumeration.

This module defines the available extraction workflows (strategies) for the system.
Each workflow represents a different approach to extracting content from PDFs.
"""

from enum import Enum


class WorkflowType(Enum):
    """Available extraction workflows.

    Each workflow uses different AI providers or extraction strategies:
    - MISTRAL: General-purpose extraction using Mistral AI via Azure OpenAI
    - TEXT_EXTRACTION: Fast extraction using pdfplumber (no AI)
    - AZURE_DOCUMENT_INTELLIGENCE: Optimized for complex tables and forms
    - OCR_WITH_IMAGES: Best for scanned documents, charts, and diagrams
    - GEMINI: High-quality extraction using Google Gemini
    """

    MISTRAL = "mistral"
    TEXT_EXTRACTION = "text_extraction"
    AZURE_DOCUMENT_INTELLIGENCE = "azure_di"
    OCR_WITH_IMAGES = "ocr_images"
    GEMINI = "gemini"

    @classmethod
    def from_string(cls, workflow_str: str) -> "WorkflowType":
        """Convert string to WorkflowType enum.

        Args:
            workflow_str: String representation of workflow type

        Returns:
            WorkflowType enum value

        Raises:
            ValueError: If workflow string is not recognized
        """
        workflow_str = workflow_str.lower().strip()

        # Handle common aliases
        alias_map = {
            "default": cls.MISTRAL,
            "text": cls.TEXT_EXTRACTION,
            "azure_di": cls.AZURE_DOCUMENT_INTELLIGENCE,
            "azure-di": cls.AZURE_DOCUMENT_INTELLIGENCE,
            "azuredi": cls.AZURE_DOCUMENT_INTELLIGENCE,
            "azure": cls.AZURE_DOCUMENT_INTELLIGENCE,
            "ocr": cls.OCR_WITH_IMAGES,
            "ocr_images": cls.OCR_WITH_IMAGES,
        }

        if workflow_str in alias_map:
            return alias_map[workflow_str]

        # Try exact match
        for workflow_type in cls:
            if workflow_type.value == workflow_str:
                return workflow_type

        raise ValueError(
            f"Unknown workflow type: {workflow_str}. "
            f"Valid options: {[wf.value for wf in cls]}"
        )

    def __str__(self) -> str:
        """Return string representation."""
        return self.value
