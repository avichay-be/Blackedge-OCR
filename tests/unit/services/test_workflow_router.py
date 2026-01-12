"""
Unit tests for Workflow Router.

Tests the intelligent routing logic that selects workflows based on query keywords.
"""

import pytest

from src.services.workflow_router import (
    get_workflow_type,
    get_workflow_description,
    list_available_workflows,
)
from src.workflows.workflow_types import WorkflowType


class TestWorkflowRouter:
    """Test cases for workflow routing."""

    def test_explicit_workflow_overrides_query(self):
        """Test that explicit workflow overrides query-based routing."""
        result = get_workflow_type(query="extract tables", explicit_workflow="gemini")
        assert result == WorkflowType.GEMINI

        result = get_workflow_type(query="use azure di", explicit_workflow="mistral")
        assert result == WorkflowType.MISTRAL

    def test_explicit_workflow_invalid(self):
        """Test that invalid explicit workflow raises ValueError."""
        with pytest.raises(ValueError, match="Invalid workflow type"):
            get_workflow_type(query="test", explicit_workflow="invalid_workflow")

    def test_text_extraction_routing(self):
        """Test routing to text extraction workflow."""
        queries = [
            "text extraction only",
            "use pdfplumber",
            "no ai please",
            "raw text extraction",
            "simple extraction",
            "plain text",
        ]

        for query in queries:
            result = get_workflow_type(query)
            assert result == WorkflowType.TEXT_EXTRACTION, f"Failed for query: {query}"

    def test_azure_di_routing(self):
        """Test routing to Azure DI workflow."""
        queries = [
            "use azure di",
            "extract with document intelligence",
            "smart tables",
            "extract forms",
            "invoice extraction",
            "structured document",
            "preserve layout",
        ]

        for query in queries:
            result = get_workflow_type(query)
            assert (
                result == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
            ), f"Failed for query: {query}"

    def test_ocr_routing(self):
        """Test routing to OCR workflow."""
        queries = [
            "ocr this document",
            "extract images",
            "process charts",
            "diagrams extraction",
            "scanned document",
            "scan to text",
            "visual content",
        ]

        for query in queries:
            result = get_workflow_type(query)
            assert result == WorkflowType.OCR_WITH_IMAGES, f"Failed for query: {query}"

    def test_gemini_routing(self):
        """Test routing to Gemini workflow."""
        queries = [
            "use gemini",
            "google extraction",
            "high quality extraction",
            "best quality",
            "maximum quality",
        ]

        for query in queries:
            result = get_workflow_type(query)
            assert result == WorkflowType.GEMINI, f"Failed for query: {query}"

    def test_mistral_default_routing(self):
        """Test that Mistral is the default workflow."""
        queries = [
            "extract all content",
            "get the data",
            "process this pdf",
            "",  # empty query
            "random query without keywords",
        ]

        for query in queries:
            result = get_workflow_type(query)
            assert result == WorkflowType.MISTRAL, f"Failed for query: {query}"

    def test_routing_priority_text_extraction(self):
        """Test that text extraction has highest priority."""
        # Even with other keywords, "text extraction" should win
        result = get_workflow_type("text extraction with tables")
        assert result == WorkflowType.TEXT_EXTRACTION

    def test_routing_priority_azure_di(self):
        """Test that Azure DI has second priority."""
        # Azure DI should win over OCR
        result = get_workflow_type("azure di for images")
        assert result == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE

    def test_routing_priority_ocr(self):
        """Test that OCR has third priority."""
        # OCR should win over Gemini
        result = get_workflow_type("ocr with gemini")
        assert result == WorkflowType.OCR_WITH_IMAGES

    def test_routing_case_insensitive(self):
        """Test that routing is case insensitive."""
        assert get_workflow_type("USE GEMINI") == WorkflowType.GEMINI
        assert get_workflow_type("Azure DI") == WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
        assert get_workflow_type("OCR") == WorkflowType.OCR_WITH_IMAGES

    def test_get_workflow_description(self):
        """Test workflow descriptions."""
        for workflow_type in WorkflowType:
            description = get_workflow_description(workflow_type)
            assert isinstance(description, str)
            assert len(description) > 0
            assert "Best for" in description or "best for" in description.lower()

    def test_list_available_workflows(self):
        """Test listing all workflows."""
        workflows = list_available_workflows()

        assert isinstance(workflows, dict)
        assert len(workflows) == 5
        assert "mistral" in workflows
        assert "text_extraction" in workflows
        assert "azure_di" in workflows
        assert "ocr_images" in workflows
        assert "gemini" in workflows

        # Check that all have descriptions
        for workflow_name, description in workflows.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_empty_query(self):
        """Test that empty query defaults to Mistral."""
        assert get_workflow_type("") == WorkflowType.MISTRAL
        assert get_workflow_type("   ") == WorkflowType.MISTRAL

    def test_none_query(self):
        """Test that None query defaults to Mistral."""
        assert get_workflow_type(None) == WorkflowType.MISTRAL
