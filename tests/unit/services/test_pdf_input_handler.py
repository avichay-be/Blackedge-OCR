"""
Unit tests for PDFInputHandler.

Tests PDF file upload and base64 decoding.
"""

import pytest
import base64
import os

from src.services.pdf_input_handler import PDFInputHandler


class TestPDFInputHandler:
    """Test cases for PDFInputHandler."""

    @pytest.mark.asyncio
    async def test_decode_base64_pdf_valid(self):
        """Test decoding valid base64 PDF."""
        handler = PDFInputHandler()

        # Create minimal valid PDF
        pdf_content = b"%PDF-1.4\n%Test PDF\n%%EOF"
        base64_content = base64.b64encode(pdf_content).decode("utf-8")

        # Decode
        pdf_path = handler.decode_base64_pdf(base64_content, filename="test.pdf")

        # Verify
        assert os.path.exists(pdf_path)
        assert pdf_path in handler.temp_files

        # Cleanup
        await handler.cleanup()
        assert not os.path.exists(pdf_path)

    def test_decode_base64_pdf_invalid(self):
        """Test decoding invalid base64 string."""
        handler = PDFInputHandler()

        with pytest.raises(ValueError, match="Invalid base64 string"):
            handler.decode_base64_pdf("not-valid-base64!!!")

    def test_decode_base64_pdf_not_pdf(self):
        """Test decoding base64 that's not a PDF."""
        handler = PDFInputHandler()

        # Valid base64 but not a PDF
        content = b"This is not a PDF file"
        base64_content = base64.b64encode(content).decode("utf-8")

        with pytest.raises(ValueError, match="Invalid PDF file"):
            handler.decode_base64_pdf(base64_content)

    def test_is_valid_pdf(self):
        """Test PDF validation."""
        handler = PDFInputHandler()

        # Valid PDF
        assert handler._is_valid_pdf(b"%PDF-1.4\nContent")

        # Invalid PDF
        assert not handler._is_valid_pdf(b"Not a PDF")
        assert not handler._is_valid_pdf(b"")

    @pytest.mark.asyncio
    async def test_cleanup_multiple_files(self):
        """Test cleanup of multiple temp files."""
        handler = PDFInputHandler()

        # Create multiple files
        pdf_content = b"%PDF-1.4\n%%EOF"
        base64_content = base64.b64encode(pdf_content).decode("utf-8")

        path1 = handler.decode_base64_pdf(base64_content)
        path2 = handler.decode_base64_pdf(base64_content)

        # Verify both exist
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert len(handler.temp_files) == 2

        # Cleanup
        await handler.cleanup()

        # Verify both deleted
        assert not os.path.exists(path1)
        assert not os.path.exists(path2)
        assert len(handler.temp_files) == 0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        pdf_content = b"%PDF-1.4\n%%EOF"
        base64_content = base64.b64encode(pdf_content).decode("utf-8")

        async with PDFInputHandler() as handler:
            pdf_path = handler.decode_base64_pdf(base64_content)
            assert os.path.exists(pdf_path)

        # Should be cleaned up after exiting context
        assert not os.path.exists(pdf_path)

    def test_get_temp_files(self):
        """Test getting list of temp files."""
        handler = PDFInputHandler()
        pdf_content = b"%PDF-1.4\n%%EOF"
        base64_content = base64.b64encode(pdf_content).decode("utf-8")

        path = handler.decode_base64_pdf(base64_content)
        temp_files = handler.get_temp_files()

        assert path in temp_files
        assert len(temp_files) == 1
