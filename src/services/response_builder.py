"""
Response Builder.

This module builds API responses in various formats (JSON, ZIP).
"""

import io
import json
import zipfile
import logging
from typing import Dict, Any
from fastapi.responses import StreamingResponse, JSONResponse

from src.models.workflow_models import WorkflowResult

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Build API responses in different formats.

    Supports:
    - JSON responses with full content and metadata
    - ZIP responses with page-by-page markdown files
    """

    def build_json_response(self, result: WorkflowResult) -> Dict[str, Any]:
        """Build JSON response from workflow result.

        Args:
            result: WorkflowResult from workflow execution

        Returns:
            Dictionary with status, content, metadata, and validation report

        Example:
            {
                "status": "success",
                "content": "Extracted text...",
                "metadata": {"workflow": "mistral", "pages": 5},
                "validation_report": {"similarity": 0.98},
                "sections": [...]
            }
        """
        response = {
            "status": "success",
            "content": result.content,
            "metadata": result.metadata,
        }

        # Add validation report if present
        if result.validation_report:
            response["validation_report"] = result.validation_report

        # Add sections if present and requested
        if result.sections:
            response["sections"] = [
                {
                    "page_number": section.page_number,
                    "content": section.content,
                    "metadata": section.metadata if section.metadata else {},
                }
                for section in result.sections
            ]

        logger.info(
            f"Built JSON response: {len(result.content)} chars, "
            f"{len(result.sections) if result.sections else 0} sections"
        )

        return response

    def build_zip_response(
        self,
        result: WorkflowResult,
        filename: str = "extraction.zip",
        include_sections: bool = True,
    ) -> StreamingResponse:
        """Build ZIP response with markdown files.

        Creates a ZIP archive containing:
        - full_content.md: Complete extracted text
        - page_N.md: Individual page content (if include_sections=True)
        - metadata.json: Extraction metadata
        - validation_report.json: Validation report (if present)

        Args:
            result: WorkflowResult from workflow execution
            filename: ZIP filename for Content-Disposition header
            include_sections: Whether to include individual page files

        Returns:
            StreamingResponse with ZIP content
        """
        logger.info(f"Building ZIP response: {filename}")

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add full content as markdown
            zip_file.writestr("full_content.md", result.content)
            logger.debug("Added full_content.md to ZIP")

            # Add individual page sections
            if include_sections and result.sections:
                for section in result.sections:
                    filename_section = f"page_{section.page_number:04d}.md"
                    zip_file.writestr(filename_section, section.content)

                logger.debug(f"Added {len(result.sections)} page files to ZIP")

            # Add metadata as JSON
            metadata_json = json.dumps(result.metadata, indent=2)
            zip_file.writestr("metadata.json", metadata_json)
            logger.debug("Added metadata.json to ZIP")

            # Add validation report if present
            if result.validation_report:
                validation_json = json.dumps(result.validation_report, indent=2)
                zip_file.writestr("validation_report.json", validation_json)
                logger.debug("Added validation_report.json to ZIP")

            # Add README
            readme_content = self._generate_readme(result)
            zip_file.writestr("README.md", readme_content)
            logger.debug("Added README.md to ZIP")

        # Seek to beginning
        zip_buffer.seek(0)

        logger.info(f"ZIP response built: {zip_buffer.getbuffer().nbytes} bytes")

        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    def _generate_readme(self, result: WorkflowResult) -> str:
        """Generate README content for ZIP archive.

        Args:
            result: WorkflowResult from workflow execution

        Returns:
            Markdown-formatted README content
        """
        pages = result.metadata.get("pages", "Unknown")
        workflow = result.metadata.get("workflow", "Unknown")
        provider = result.metadata.get("provider", "Unknown")

        readme = f"""# PDF Extraction Results

## Summary
- **Workflow**: {workflow}
- **Provider**: {provider}
- **Pages Processed**: {pages}
- **Content Length**: {len(result.content):,} characters

## Files Included

- `full_content.md`: Complete extracted text from all pages
- `metadata.json`: Extraction metadata and processing information
"""

        # Add sections info
        if result.sections:
            readme += f"- `page_NNNN.md`: Individual page content ({len(result.sections)} files)\n"

        # Add validation info
        if result.validation_report:
            readme += (
                "- `validation_report.json`: Validation and quality check results\n"
            )

            if result.validation_report.get("used_secondary"):
                readme += "\n⚠️ **Note**: Secondary extraction was used due to "
                reason = result.validation_report.get("reason", "unknown reason")
                readme += f"{reason}\n"

        # Add metadata details
        readme += "\n## Metadata Details\n\n"
        for key, value in result.metadata.items():
            if key not in ["workflow", "provider", "pages"]:
                readme += f"- **{key}**: {value}\n"

        return readme

    def build_error_response(
        self, error: str, status_code: int = 500, details: Dict[str, Any] = None
    ) -> JSONResponse:
        """Build error response.

        Args:
            error: Error message
            status_code: HTTP status code
            details: Optional additional error details

        Returns:
            JSONResponse with error information
        """
        response_data = {
            "status": "error",
            "error": error,
        }

        if details:
            response_data["details"] = details

        logger.error(f"Building error response: {error} (status={status_code})")

        return JSONResponse(status_code=status_code, content=response_data)
