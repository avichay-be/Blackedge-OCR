"""
Core application constants.

This module defines application-wide constants used across the codebase,
including content separators, processing limits, and workflow keywords.

Example:
    from src.core.constants import CONTENT_SEPARATOR, MAX_FILE_SIZE_MB

    content = page1 + CONTENT_SEPARATOR + page2
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError("File too large")
"""

# Content Formatting
CONTENT_SEPARATOR = "\n---PAGE-BREAK---\n"
"""Separator used between PDF pages in extracted content."""

SECTION_SEPARATOR = "\n\n---\n\n"
"""Separator used between document sections."""

# Processing Configuration
DEFAULT_CHUNK_SIZE = 50
"""Default number of pages to process in a single chunk."""

MAX_CONCURRENT_REQUESTS = 5
"""Maximum number of concurrent API requests allowed."""

REQUEST_TIMEOUT = 120
"""Default request timeout in seconds."""

# Workflow Keywords
WORKFLOW_KEYWORDS = {
    "text_extraction": ["text extraction", "pdfplumber", "no ai", "simple extract"],
    "azure_di": ["azure di", "document intelligence", "smart tables", "form recognition"],
    "ocr_images": ["ocr", "images", "charts", "diagrams", "vision", "scanned"],
    "gemini": ["gemini", "google"],
    "mistral": ["mistral", "default"]
}
"""Keywords used to determine which workflow to use based on user query."""

# File Limits
MAX_FILE_SIZE_MB = 50
"""Maximum allowed PDF file size in megabytes."""

ALLOWED_EXTENSIONS = [".pdf"]
"""List of allowed file extensions."""

# HTTP Status Codes
HTTP_SUCCESS = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# Retry Configuration
MAX_RETRIES = 3
"""Maximum number of retry attempts for failed API calls."""

RETRY_BACKOFF_FACTOR = 2
"""Exponential backoff factor for retries (seconds)."""

RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
"""HTTP status codes that trigger automatic retry."""

# Logging
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""Default log message format."""

# API Rate Limits (requests per minute)
RATE_LIMITS = {
    "mistral": 60,
    "openai": 50,
    "gemini": 60,
    "azure_di": 30
}
"""Rate limits for different AI providers (requests per minute)."""
