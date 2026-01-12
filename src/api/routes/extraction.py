"""
Extraction Routes.

Main PDF extraction endpoints for JSON and ZIP responses.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from typing import Optional

from src.api.models import ExtractionResponse, Base64ExtractionRequest
from src.services.pdf_input_handler import PDFInputHandler
from src.services.workflow_orchestrator import get_workflow_orchestrator
from src.services.response_builder import ResponseBuilder
from src.core.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract-json", response_model=ExtractionResponse)
async def extract_json(
    file: UploadFile = File(..., description="PDF file to extract"),
    query: str = Form(default="", description="User query for context"),
    enable_validation: Optional[bool] = Form(
        default=None, description="Enable cross-validation"
    ),
    workflow: Optional[str] = Form(
        default=None, description="Explicit workflow to use"
    ),
    _: bool = Depends(verify_api_key),
):
    """Extract PDF content and return as JSON.

    Uploads a PDF file and extracts its content using the specified workflow.
    Returns full content, metadata, and optional validation report in JSON format.

    Args:
        file: PDF file upload
        query: User query providing extraction context
        enable_validation: Override global validation setting
        workflow: Explicit workflow name (optional)

    Returns:
        ExtractionResponse with content and metadata

    Raises:
        HTTPException: If extraction fails
    """
    pdf_handler = PDFInputHandler()
    orchestrator = get_workflow_orchestrator()
    response_builder = ResponseBuilder()

    try:
        logger.info(
            f"JSON extraction requested: {file.filename}, "
            f"query='{query[:50]}...', workflow={workflow}"
        )

        # Save uploaded file
        pdf_path = await pdf_handler.save_uploaded_file(file)

        # Execute workflow
        result = await orchestrator.execute_workflow(
            pdf_path=pdf_path,
            query=query,
            enable_validation=enable_validation,
            explicit_workflow=workflow,
        )

        # Build JSON response
        response = response_builder.build_json_response(result)

        logger.info(
            f"JSON extraction completed: {result.metadata.get('pages', 'N/A')} pages, "
            f"{len(result.content)} chars"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        # Always cleanup temp files
        await pdf_handler.cleanup()


@router.post("/extract-zip")
async def extract_zip(
    file: UploadFile = File(..., description="PDF file to extract"),
    query: str = Form(default="", description="User query for context"),
    enable_validation: Optional[bool] = Form(
        default=None, description="Enable cross-validation"
    ),
    workflow: Optional[str] = Form(
        default=None, description="Explicit workflow to use"
    ),
    include_sections: bool = Form(
        default=True, description="Include individual page files"
    ),
    _: bool = Depends(verify_api_key),
):
    """Extract PDF content and return as ZIP archive.

    Uploads a PDF file and extracts its content using the specified workflow.
    Returns a ZIP archive containing markdown files for full content,
    individual pages, and metadata.

    Args:
        file: PDF file upload
        query: User query providing extraction context
        enable_validation: Override global validation setting
        workflow: Explicit workflow name (optional)
        include_sections: Include individual page files in ZIP

    Returns:
        StreamingResponse with ZIP archive

    Raises:
        HTTPException: If extraction fails
    """
    pdf_handler = PDFInputHandler()
    orchestrator = get_workflow_orchestrator()
    response_builder = ResponseBuilder()

    try:
        logger.info(
            f"ZIP extraction requested: {file.filename}, "
            f"query='{query[:50]}...', workflow={workflow}"
        )

        # Save uploaded file
        pdf_path = await pdf_handler.save_uploaded_file(file)

        # Execute workflow
        result = await orchestrator.execute_workflow(
            pdf_path=pdf_path,
            query=query,
            enable_validation=enable_validation,
            explicit_workflow=workflow,
        )

        # Build ZIP response
        # Use original filename for ZIP
        zip_filename = (
            file.filename.replace(".pdf", ".zip") if file.filename else "extraction.zip"
        )

        response = response_builder.build_zip_response(
            result, filename=zip_filename, include_sections=include_sections
        )

        logger.info(
            f"ZIP extraction completed: {result.metadata.get('pages', 'N/A')} pages"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        # Always cleanup temp files
        await pdf_handler.cleanup()


@router.post("/extract-base64-json", response_model=ExtractionResponse)
async def extract_base64_json(
    request: Base64ExtractionRequest,
    _: bool = Depends(verify_api_key),
):
    """Extract PDF from base64 and return as JSON.

    Accepts base64-encoded PDF content and extracts using the specified workflow.

    Args:
        request: Base64ExtractionRequest with PDF content and parameters

    Returns:
        ExtractionResponse with content and metadata

    Raises:
        HTTPException: If extraction fails
    """
    pdf_handler = PDFInputHandler()
    orchestrator = get_workflow_orchestrator()
    response_builder = ResponseBuilder()

    try:
        logger.info(
            f"Base64 JSON extraction requested: "
            f"query='{request.query[:50]}...', workflow={request.workflow}"
        )

        # Decode base64 PDF
        pdf_path = pdf_handler.decode_base64_pdf(
            request.pdf_content, filename=request.filename
        )

        # Execute workflow
        result = await orchestrator.execute_workflow(
            pdf_path=pdf_path,
            query=request.query,
            enable_validation=request.enable_validation,
            explicit_workflow=request.workflow,
        )

        # Build JSON response
        response = response_builder.build_json_response(result)

        logger.info(
            f"Base64 extraction completed: {result.metadata.get('pages', 'N/A')} pages"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        # Always cleanup temp files
        await pdf_handler.cleanup()
