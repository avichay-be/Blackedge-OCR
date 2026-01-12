"""
Text Extraction Handler.

This handler provides fast PDF text extraction using pdfplumber without AI processing.
Best for: Simple text extraction where AI enhancement is not needed.
"""

import time
import logging
from typing import Optional, List
import pdfplumber

from src.services.workflows.base_handler import BaseWorkflowHandler
from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import WorkflowResult, ExtractedSection
from src.core.error_handling import ExtractionError
from src.core.constants import CONTENT_SEPARATOR

logger = logging.getLogger(__name__)


class TextExtractionHandler(BaseWorkflowHandler):
    """Handler for simple text extraction using pdfplumber.

    This workflow does not use any AI providers. It simply extracts
    raw text from the PDF using pdfplumber.

    Advantages:
        - Fast (no API calls)
        - Free (no API costs)
        - Works offline
        - Good for clean, text-based PDFs

    Limitations:
        - No semantic understanding
        - Poor handling of complex layouts
        - No OCR for images
        - Limited table extraction
    """

    def __init__(self):
        """Initialize text extraction handler."""
        super().__init__(WorkflowType.TEXT_EXTRACTION)

    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute text extraction workflow.

        Args:
            pdf_path: Path to PDF file
            query: User query (not used in this workflow)
            enable_validation: Not used (no validation for text-only extraction)

        Returns:
            WorkflowResult with extracted text and metadata

        Raises:
            ExtractionError: If PDF cannot be read or processed
        """
        start_time = time.time()
        self._log_start(pdf_path, query)

        try:
            sections = await self._extract_text(pdf_path)

            # Combine all sections
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            # Build metadata
            metadata = {
                "workflow": self.workflow_type.value,
                "pages": len(sections),
                "processing_time_seconds": time.time() - start_time,
                "provider": "pdfplumber",
                "ai_used": False,
            }

            execution_time = time.time() - start_time
            self._log_complete(len(content), metadata, execution_time)

            return WorkflowResult(
                content=content,
                metadata=metadata,
                sections=sections,
                validation_report=None,
            )

        except Exception as e:
            logger.error(f"Text extraction failed: {e}", exc_info=True)
            raise ExtractionError(f"Failed to extract text from PDF: {e}")

    async def _extract_text(self, pdf_path: str) -> List[ExtractedSection]:
        """Extract text from PDF using pdfplumber.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of ExtractedSection objects, one per page

        Raises:
            ExtractionError: If PDF cannot be read
        """
        sections = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Extracting text from {total_pages} pages")

                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    text = page.extract_text() or ""

                    # Try to extract tables if present
                    tables = page.extract_tables()
                    if tables:
                        table_text = self._format_tables(tables)
                        if table_text:
                            text += f"\n\n{table_text}"

                    # Create section
                    section = ExtractedSection(
                        page_number=page_num,
                        content=text,
                        metadata={
                            "char_count": len(text),
                            "has_tables": len(tables) > 0 if tables else False,
                            "page_width": page.width,
                            "page_height": page.height,
                        },
                    )
                    sections.append(section)

                    logger.debug(
                        f"Extracted page {page_num}/{total_pages} | "
                        f"{len(text)} chars | "
                        f"{len(tables) if tables else 0} tables"
                    )

        except FileNotFoundError:
            raise ExtractionError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise ExtractionError(f"Failed to read PDF: {e}")

        return sections

    def _format_tables(self, tables: List[List[List[str]]]) -> str:
        """Format extracted tables as text.

        Args:
            tables: List of tables, where each table is a list of rows

        Returns:
            Formatted table text
        """
        if not tables:
            return ""

        formatted_tables = []

        for table_idx, table in enumerate(tables, start=1):
            if not table:
                continue

            # Format table
            formatted_rows = []
            for row in table:
                if row:
                    # Filter out None values and join with |
                    cleaned_row = [str(cell) if cell else "" for cell in row]
                    formatted_rows.append(" | ".join(cleaned_row))

            if formatted_rows:
                table_text = f"TABLE {table_idx}:\n" + "\n".join(formatted_rows)
                formatted_tables.append(table_text)

        return "\n\n".join(formatted_tables) if formatted_tables else ""
