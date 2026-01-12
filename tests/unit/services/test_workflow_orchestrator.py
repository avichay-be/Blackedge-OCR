"""
Unit tests for Workflow Orchestrator.

Tests the central orchestration of workflow execution.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.workflow_orchestrator import (
    WorkflowOrchestrator,
    get_workflow_orchestrator,
)
from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import WorkflowResult, ExtractedSection
from src.core.error_handling import ExtractionError


@pytest.mark.asyncio
class TestWorkflowOrchestrator:
    """Test cases for WorkflowOrchestrator."""

    def test_singleton_pattern(self):
        """Test that orchestrator follows singleton pattern."""
        orchestrator1 = WorkflowOrchestrator()
        orchestrator2 = WorkflowOrchestrator()

        assert orchestrator1 is orchestrator2

    def test_get_orchestrator_singleton(self):
        """Test that get_workflow_orchestrator returns singleton."""
        orchestrator1 = get_workflow_orchestrator()
        orchestrator2 = get_workflow_orchestrator()

        assert orchestrator1 is orchestrator2
        assert isinstance(orchestrator1, WorkflowOrchestrator)

    def test_initialization_creates_handlers(self):
        """Test that initialization creates all handlers."""
        orchestrator = WorkflowOrchestrator()

        assert len(orchestrator.workflow_handlers) == 5
        assert WorkflowType.TEXT_EXTRACTION in orchestrator.workflow_handlers
        assert WorkflowType.MISTRAL in orchestrator.workflow_handlers
        assert (
            WorkflowType.AZURE_DOCUMENT_INTELLIGENCE
            in orchestrator.workflow_handlers
        )
        assert WorkflowType.OCR_WITH_IMAGES in orchestrator.workflow_handlers
        assert WorkflowType.GEMINI in orchestrator.workflow_handlers

    def test_get_handler_success(self):
        """Test getting a specific handler."""
        orchestrator = WorkflowOrchestrator()

        handler = orchestrator.get_handler(WorkflowType.MISTRAL)
        assert handler is not None
        assert handler.workflow_type == WorkflowType.MISTRAL

    def test_get_handler_invalid(self):
        """Test getting handler with invalid workflow type."""
        orchestrator = WorkflowOrchestrator()

        # Create a fake enum value (this shouldn't normally happen)
        # We'll test with a string instead
        with pytest.raises(ValueError, match="Unknown workflow type"):
            # We can't easily create an invalid WorkflowType enum,
            # so we'll just verify the dict doesn't have unexpected keys
            orchestrator.get_handler("invalid")  # type: ignore

    def test_list_workflows(self):
        """Test listing all available workflows."""
        orchestrator = WorkflowOrchestrator()

        workflows = orchestrator.list_workflows()

        assert len(workflows) == 5
        assert "text_extraction" in workflows
        assert "mistral" in workflows
        assert "azure_di" in workflows
        assert "ocr_images" in workflows
        assert "gemini" in workflows

    @patch("src.services.workflow_orchestrator.get_workflow_type")
    async def test_execute_workflow_with_routing(self, mock_get_workflow_type):
        """Test workflow execution with automatic routing."""
        mock_get_workflow_type.return_value = WorkflowType.MISTRAL

        orchestrator = WorkflowOrchestrator()

        # Mock the handler's execute method
        mock_result = WorkflowResult(
            content="Test content",
            metadata={"workflow": "mistral", "pages": 1},
        )
        orchestrator.workflow_handlers[WorkflowType.MISTRAL].execute = AsyncMock(
            return_value=mock_result
        )

        # Execute workflow
        result = await orchestrator.execute_workflow(
            pdf_path="/test/path.pdf", query="extract data"
        )

        assert result.content == "Test content"
        assert result.metadata["workflow"] == "mistral"
        mock_get_workflow_type.assert_called_once_with("extract data", None)

    @patch("src.services.workflow_orchestrator.get_workflow_type")
    async def test_execute_workflow_with_explicit_workflow(
        self, mock_get_workflow_type
    ):
        """Test workflow execution with explicit workflow type."""
        mock_get_workflow_type.return_value = WorkflowType.GEMINI

        orchestrator = WorkflowOrchestrator()

        # Mock the handler's execute method
        mock_result = WorkflowResult(
            content="Gemini content", metadata={"workflow": "gemini", "pages": 2}
        )
        orchestrator.workflow_handlers[WorkflowType.GEMINI].execute = AsyncMock(
            return_value=mock_result
        )

        # Execute workflow with explicit type
        result = await orchestrator.execute_workflow(
            pdf_path="/test/path.pdf", query="extract", explicit_workflow="gemini"
        )

        assert result.content == "Gemini content"
        assert result.metadata["workflow"] == "gemini"
        mock_get_workflow_type.assert_called_once_with("extract", "gemini")

    @patch("src.services.workflow_orchestrator.get_workflow_type")
    async def test_execute_workflow_with_validation(self, mock_get_workflow_type):
        """Test workflow execution with validation enabled."""
        mock_get_workflow_type.return_value = WorkflowType.MISTRAL

        orchestrator = WorkflowOrchestrator()

        # Mock handler
        mock_result = WorkflowResult(
            content="Content",
            metadata={"workflow": "mistral"},
            validation_report={"similarity": 0.98},
        )
        orchestrator.workflow_handlers[WorkflowType.MISTRAL].execute = AsyncMock(
            return_value=mock_result
        )

        # Execute with validation
        result = await orchestrator.execute_workflow(
            pdf_path="/test/path.pdf", query="extract", enable_validation=True
        )

        assert result.content == "Content"

        # Verify execute was called with enable_validation=True
        orchestrator.workflow_handlers[WorkflowType.MISTRAL].execute.assert_called_once()
        call_kwargs = orchestrator.workflow_handlers[
            WorkflowType.MISTRAL
        ].execute.call_args[1]
        assert call_kwargs["enable_validation"] is True

    @patch("src.services.workflow_orchestrator.get_workflow_type")
    async def test_execute_workflow_handler_error(self, mock_get_workflow_type):
        """Test that handler errors are properly wrapped."""
        mock_get_workflow_type.return_value = WorkflowType.MISTRAL

        orchestrator = WorkflowOrchestrator()

        # Mock handler to raise error
        orchestrator.workflow_handlers[WorkflowType.MISTRAL].execute = AsyncMock(
            side_effect=Exception("Handler failed")
        )

        # Execute should raise ExtractionError
        with pytest.raises(ExtractionError, match="Failed to execute"):
            await orchestrator.execute_workflow(
                pdf_path="/test/path.pdf", query="extract"
            )

    @patch("src.services.workflow_orchestrator.get_workflow_type")
    async def test_execute_workflow_all_types(self, mock_get_workflow_type):
        """Test execution with all workflow types."""
        orchestrator = WorkflowOrchestrator()

        for workflow_type in WorkflowType:
            mock_get_workflow_type.return_value = workflow_type

            # Mock handler
            mock_result = WorkflowResult(
                content=f"Content from {workflow_type.value}",
                metadata={"workflow": workflow_type.value},
            )
            orchestrator.workflow_handlers[workflow_type].execute = AsyncMock(
                return_value=mock_result
            )

            # Execute
            result = await orchestrator.execute_workflow(
                pdf_path="/test/path.pdf", query="test query"
            )

            assert result.content == f"Content from {workflow_type.value}"
            assert result.metadata["workflow"] == workflow_type.value
