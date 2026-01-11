"""
Unit tests for Workflow Types.

Tests the workflow enumeration and type conversion.
"""

import pytest

from src.workflows.workflow_types import WorkflowType


class TestWorkflowType:
    """Test cases for WorkflowType enum."""

    def test_enum_values(self):
        """Test that all expected workflow types exist."""
        assert WorkflowType.MISTRAL.value == "mistral"
        assert WorkflowType.TEXT_EXTRACTION.value == "text_extraction"
        assert WorkflowType.AZURE_DOCUMENT_INTELLIGENCE.value == "azure_di"
        assert WorkflowType.OCR_WITH_IMAGES.value == "ocr_images"
        assert WorkflowType.GEMINI.value == "gemini"

    def test_from_string_exact_match(self):
        """Test conversion from exact string match."""
        assert WorkflowType.from_string("mistral") == WorkflowType.MISTRAL
        assert (
            WorkflowType.from_string("text_extraction") == WorkflowType.TEXT_EXTRACTION
        )
        assert (
            WorkflowType.from_string("azure_di")
            == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
        )
        assert WorkflowType.from_string("ocr_images") == WorkflowType.OCR_WITH_IMAGES
        assert WorkflowType.from_string("gemini") == WorkflowType.GEMINI

    def test_from_string_case_insensitive(self):
        """Test that string conversion is case insensitive."""
        assert WorkflowType.from_string("MISTRAL") == WorkflowType.MISTRAL
        assert WorkflowType.from_string("Mistral") == WorkflowType.MISTRAL
        assert WorkflowType.from_string("GEMINI") == WorkflowType.GEMINI

    def test_from_string_with_whitespace(self):
        """Test that string conversion handles whitespace."""
        assert WorkflowType.from_string("  mistral  ") == WorkflowType.MISTRAL
        assert WorkflowType.from_string("\tgemini\n") == WorkflowType.GEMINI

    def test_from_string_aliases(self):
        """Test that common aliases work."""
        assert WorkflowType.from_string("default") == WorkflowType.MISTRAL
        assert WorkflowType.from_string("text") == WorkflowType.TEXT_EXTRACTION
        assert (
            WorkflowType.from_string("azure")
            == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
        )
        assert (
            WorkflowType.from_string("azure-di")
            == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
        )
        assert WorkflowType.from_string("ocr") == WorkflowType.OCR_WITH_IMAGES

    def test_from_string_invalid(self):
        """Test that invalid strings raise ValueError."""
        with pytest.raises(ValueError, match="Unknown workflow type"):
            WorkflowType.from_string("invalid_workflow")

        with pytest.raises(ValueError, match="Unknown workflow type"):
            WorkflowType.from_string("foobar")

    def test_str_representation(self):
        """Test string representation."""
        assert str(WorkflowType.MISTRAL) == "mistral"
        assert str(WorkflowType.GEMINI) == "gemini"
        assert str(WorkflowType.TEXT_EXTRACTION) == "text_extraction"

    def test_all_workflow_types_count(self):
        """Test that we have exactly 5 workflow types."""
        all_types = list(WorkflowType)
        assert len(all_types) == 5
