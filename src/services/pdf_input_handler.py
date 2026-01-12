"""
PDF Input Handler.

This module handles PDF file uploads, base64 decoding, and temp file management.
"""

import os
import base64
import tempfile
import logging
from typing import List, Optional
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class PDFInputHandler:
    """Handle PDF file inputs and temporary file management.

    This class manages:
    - Uploading PDF files from FastAPI
    - Decoding base64-encoded PDFs
    - Temporary file creation and cleanup
    - Validation of PDF files
    """

    def __init__(self):
        """Initialize PDF input handler."""
        self.temp_files: List[str] = []
        logger.debug("Initialized PDFInputHandler")

    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file to temporary location.

        Args:
            file: FastAPI UploadFile object

        Returns:
            Path to saved temporary file

        Raises:
            ValueError: If file is not a PDF or is empty
            IOError: If file cannot be saved
        """
        # Validate file
        if not file.filename:
            raise ValueError("No filename provided")

        if not file.filename.lower().endswith(".pdf"):
            raise ValueError(f"File must be a PDF, got: {file.filename}")

        # Read content
        content = await file.read()

        if not content:
            raise ValueError("Uploaded file is empty")

        # Validate PDF header
        if not self._is_valid_pdf(content):
            raise ValueError("Invalid PDF file (missing PDF header)")

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="upload_"
        )

        try:
            temp_file.write(content)
            temp_file.close()

            # Track for cleanup
            self.temp_files.append(temp_file.name)

            logger.info(
                f"Saved uploaded file: {file.filename} ({len(content)} bytes) "
                f"to {temp_file.name}"
            )

            return temp_file.name

        except Exception as e:
            # Clean up temp file if save failed
            try:
                os.remove(temp_file.name)
            except:
                pass
            raise IOError(f"Failed to save uploaded file: {e}")

    def decode_base64_pdf(
        self, base64_string: str, filename: Optional[str] = None
    ) -> str:
        """Decode base64 PDF and save to temporary file.

        Args:
            base64_string: Base64-encoded PDF content
            filename: Optional original filename for logging

        Returns:
            Path to saved temporary file

        Raises:
            ValueError: If base64 string is invalid or not a PDF
            IOError: If file cannot be saved
        """
        if not base64_string:
            raise ValueError("Empty base64 string provided")

        try:
            # Decode base64
            pdf_bytes = base64.b64decode(base64_string, validate=True)

        except Exception as e:
            raise ValueError(f"Invalid base64 string: {e}")

        if not pdf_bytes:
            raise ValueError("Decoded PDF is empty")

        # Validate PDF header
        if not self._is_valid_pdf(pdf_bytes):
            raise ValueError("Invalid PDF file (missing PDF header)")

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="base64_"
        )

        try:
            temp_file.write(pdf_bytes)
            temp_file.close()

            # Track for cleanup
            self.temp_files.append(temp_file.name)

            logger.info(
                f"Decoded base64 PDF{f' ({filename})' if filename else ''}: "
                f"{len(pdf_bytes)} bytes to {temp_file.name}"
            )

            return temp_file.name

        except Exception as e:
            # Clean up temp file if save failed
            try:
                os.remove(temp_file.name)
            except:
                pass
            raise IOError(f"Failed to save decoded PDF: {e}")

    def _is_valid_pdf(self, content: bytes) -> bool:
        """Check if content is a valid PDF file.

        Args:
            content: File content bytes

        Returns:
            True if content starts with PDF header
        """
        # PDF files must start with %PDF-
        return content.startswith(b"%PDF-")

    async def cleanup(self):
        """Delete all temporary files.

        This method is safe to call multiple times and will not raise
        exceptions if files cannot be deleted.
        """
        if not self.temp_files:
            return

        logger.info(f"Cleaning up {len(self.temp_files)} temporary files")

        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Deleted temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")

        # Clear list
        self.temp_files.clear()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic cleanup.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        await self.cleanup()

    def get_temp_files(self) -> List[str]:
        """Get list of temporary files being tracked.

        Returns:
            List of temporary file paths
        """
        return self.temp_files.copy()
