"""
Error handling framework.

This module provides custom exception classes and error handling decorators
for consistent error management across the application.

Example:
    from src.core.error_handling import handle_extraction_errors, APIClientError

    @handle_extraction_errors("PDF extraction")
    async def extract_pdf(file_path: str):
        if not file_exists(file_path):
            raise APIClientError("File not found")
        # ... extraction logic
"""

import logging
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# Exception Hierarchy
class ExtractionError(Exception):
    """Base exception for all extraction-related errors."""
    pass


class APIClientError(ExtractionError):
    """
    Exception raised when external API calls fail.

    This includes timeouts, authentication errors, rate limits,
    and other API-specific failures.
    """
    pass


class ValidationError(ExtractionError):
    """
    Exception raised when validation checks fail.

    This includes invalid input data, malformed PDFs,
    and content validation failures.
    """
    pass


class ConfigurationError(ExtractionError):
    """
    Exception raised for configuration-related issues.

    This includes missing API keys, invalid settings,
    and environment configuration problems.
    """
    pass


class WorkflowError(ExtractionError):
    """
    Exception raised when workflow execution fails.

    This includes workflow routing errors, handler failures,
    and orchestration issues.
    """
    pass


class FileProcessingError(ExtractionError):
    """
    Exception raised during file processing operations.

    This includes file I/O errors, PDF parsing failures,
    and temporary file management issues.
    """
    pass


# Error Handling Decorators
def handle_extraction_errors(context: str):
    """
    Decorator for consistent error handling in extraction operations.

    Catches ExtractionError exceptions and converts them to FastAPI HTTPExceptions
    with appropriate status codes and error messages. Also handles unexpected
    exceptions with generic error responses.

    Args:
        context: Descriptive context for the operation (used in logging)

    Returns:
        Decorated function with error handling

    Example:
        @handle_extraction_errors("PDF content extraction")
        async def extract_content(pdf_path: str):
            # Your extraction logic here
            pass

    Raises:
        HTTPException: With status 500 and error details
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                logger.error(f"{context} - Validation error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation error: {str(e)}"
                )
            except ConfigurationError as e:
                logger.error(f"{context} - Configuration error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Configuration error: {str(e)}"
                )
            except APIClientError as e:
                logger.error(f"{context} - API client error: {e}")
                raise HTTPException(
                    status_code=502,
                    detail=f"External API error: {str(e)}"
                )
            except ExtractionError as e:
                logger.error(f"{context} - Extraction error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )
            except HTTPException:
                # Re-raise HTTPExceptions as-is
                raise
            except Exception as e:
                logger.exception(f"{context} - Unexpected error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                logger.error(f"{context} - Validation error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation error: {str(e)}"
                )
            except ConfigurationError as e:
                logger.error(f"{context} - Configuration error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Configuration error: {str(e)}"
                )
            except APIClientError as e:
                logger.error(f"{context} - API client error: {e}")
                raise HTTPException(
                    status_code=502,
                    detail=f"External API error: {str(e)}"
                )
            except ExtractionError as e:
                logger.error(f"{context} - Extraction error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )
            except HTTPException:
                # Re-raise HTTPExceptions as-is
                raise
            except Exception as e:
                logger.exception(f"{context} - Unexpected error: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_and_raise(
    exception_class: type[ExtractionError],
    message: str,
    logger_instance: logging.Logger = logger
) -> None:
    """
    Log an error message and raise an exception.

    Utility function to consistently log errors before raising exceptions.

    Args:
        exception_class: Exception class to raise
        message: Error message
        logger_instance: Logger instance to use (default: module logger)

    Example:
        log_and_raise(APIClientError, "API request failed", logger)

    Raises:
        exception_class: The specified exception with the given message
    """
    logger_instance.error(message)
    raise exception_class(message)


def handle_file_errors(func: Callable) -> Callable:
    """
    Decorator for handling file operation errors.

    Converts common file operation exceptions (FileNotFoundError, PermissionError, etc.)
    into FileProcessingError with appropriate messages.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with file error handling

    Example:
        @handle_file_errors
        def read_pdf(file_path: str):
            with open(file_path, 'rb') as f:
                return f.read()
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            raise FileProcessingError(f"File not found: {e}")
        except PermissionError as e:
            raise FileProcessingError(f"Permission denied: {e}")
        except IsADirectoryError as e:
            raise FileProcessingError(f"Expected file, got directory: {e}")
        except IOError as e:
            raise FileProcessingError(f"I/O error: {e}")

    return wrapper
