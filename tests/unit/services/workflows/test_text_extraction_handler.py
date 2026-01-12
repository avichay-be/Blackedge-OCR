"""
Unit tests for Text Extraction Handler.

Tests the pdfplumber-based text extraction workflow.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import pdfplumber

from src.services.workflows.text_extraction_handler import TextExtractionHandler
from src.workflows.workflow_types import WorkflowType
from src.core.error_handling import ExtractionError


@pytest.mark.asyncio
class TestTextExtractionHandler:
    """Test cases for TextExtractionHandler."""

    def test_initialization(self):
        """Test handler initialization."""
        handler = TextExtractionHandler()

        assert handler.workflow_type == WorkflowType.TEXT_EXTRACTION
        assert isinstance(handler, TextExtractionHandler)

    @patch("src.services.workflows.text_extraction_handler.pdfplumber.open")
    async def test_execute_success(self, mock_pdfplumber_open):
        """Test successful text extraction."""
        # Mock PDF with 2 pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page1.extract_tables.return_value = []
        mock_page1.width = 612
        mock_page1.height = 792

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_page2.extract_tables.return_value = []
        mock_page2.width = 612
        mock_page2.height = 792

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)

        mock_pdfplumber_open.return_value = mock_pdf

        # Execute
        handler = TextExtractionHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract text")

        # Verify result
        assert "Page 1 content" in result.content
        assert "Page 2 content" in result.content
        assert result.metadata["workflow"] == "text_extraction"
        assert result.metadata["pages"] == 2
        assert result.metadata["provider"] == "pdfplumber"
        assert result.metadata["ai_used"] is False
        assert len(result.sections) == 2

    @patch("src.services.workflows.text_extraction_handler.pdfplumber.open")
    async def test_execute_with_tables(self, mock_pdfplumber_open):
        """Test extraction with tables."""
        # Mock page with table
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page text"
        mock_page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Row1Col1", "Row1Col2"], ["Row2Col1", "Row2Col2"]]
        ]
        mock_page.width = 612
        mock_page.height = 792

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)

        mock_pdfplumber_open.return_value = mock_pdf

        # Execute
        handler = TextExtractionHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract")

        # Verify table was included
        assert "Page text" in result.content
        assert "TABLE 1:" in result.content
        assert "Header1 | Header2" in result.content
        assert result.sections[0].metadata["has_tables"] is True

    @patch("src.services.workflows.text_extraction_handler.pdfplumber.open")
    async def test_execute_empty_page(self, mock_pdfplumber_open):
        """Test extraction from empty page."""
        # Mock empty page
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # pdfplumber returns None for empty
        mock_page.extract_tables.return_value = []
        mock_page.width = 612
        mock_page.height = 792

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)

        mock_pdfplumber_open.return_value = mock_pdf

        # Execute
        handler = TextExtractionHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract")

        # Should handle empty page gracefully
        assert result.content == ""  # Empty string
        assert result.sections[0].content == ""

    @patch("src.services.workflows.text_extraction_handler.pdfplumber.open")
    async def test_execute_file_not_found(self, mock_pdfplumber_open):
        """Test extraction with missing file."""
        mock_pdfplumber_open.side_effect = FileNotFoundError("File not found")

        handler = TextExtractionHandler()

        with pytest.raises(ExtractionError, match="PDF file not found"):
            await handler.execute(pdf_path="/missing/file.pdf", query="extract")

    @patch("src.services.workflows.text_extraction_handler.pdfplumber.open")
    async def test_execute_pdf_read_error(self, mock_pdfplumber_open):
        """Test extraction with PDF read error."""
        mock_pdfplumber_open.side_effect = Exception("Corrupted PDF")

        handler = TextExtractionHandler()

        with pytest.raises(ExtractionError, match="Failed to read PDF"):
            await handler.execute(pdf_path="/test/corrupted.pdf", query="extract")

    def test_format_tables_empty(self):
        """Test table formatting with empty input."""
        handler = TextExtractionHandler()

        result = handler._format_tables([])
        assert result == ""

        result = handler._format_tables(None)
        assert result == ""

    def test_format_tables_single_table(self):
        """Test formatting a single table."""
        handler = TextExtractionHandler()

        table = [["A", "B"], ["1", "2"], ["3", "4"]]

        result = handler._format_tables([table])

        assert "TABLE 1:" in result
        assert "A | B" in result
        assert "1 | 2" in result
        assert "3 | 4" in result

    def test_format_tables_multiple_tables(self):
        """Test formatting multiple tables."""
        handler = TextExtractionHandler()

        table1 = [["A", "B"]]
        table2 = [["C", "D"]]

        result = handler._format_tables([table1, table2])

        assert "TABLE 1:" in result
        assert "TABLE 2:" in result
        assert "A | B" in result
        assert "C | D" in result

    def test_format_tables_with_none_values(self):
        """Test table formatting handles None values."""
        handler = TextExtractionHandler()

        table = [["A", None, "C"], [None, "B", None]]

        result = handler._format_tables([table])

        assert "TABLE 1:" in result
        assert "A |  | C" in result  # Empty string for None
