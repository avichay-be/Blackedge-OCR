"""
Core utility functions.

This module provides utility functions for PDF processing, file operations,
and common transformations used throughout the application.

Example:
    from src.core.utils import encode_pdf_to_base64, get_pdf_page_count

    pdf_base64 = encode_pdf_to_base64("/path/to/file.pdf")
    page_count = get_pdf_page_count("/path/to/file.pdf")
"""

import base64
from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader
from src.core.constants import MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS


def encode_pdf_to_base64(pdf_path: str) -> str:
    """
    Convert PDF file to base64-encoded string.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Base64-encoded string representation of the PDF

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        IOError: If file cannot be read

    Example:
        >>> encoded = encode_pdf_to_base64("document.pdf")
        >>> print(encoded[:50])
        'JVBERi0xLjQKJeLjz9MKMSAwIG9iaiA8PAovU...'
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        return base64.b64encode(pdf_bytes).decode("utf-8")


def decode_base64_to_pdf(base64_string: str, output_path: str) -> str:
    """
    Decode base64 string and save as PDF file.

    Args:
        base64_string: Base64-encoded PDF data
        output_path: Path where PDF should be saved

    Returns:
        Path to the saved PDF file

    Raises:
        ValueError: If base64 string is invalid
        IOError: If file cannot be written

    Example:
        >>> path = decode_base64_to_pdf(encoded_data, "output.pdf")
        >>> print(path)
        'output.pdf'
    """
    try:
        pdf_bytes = base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Invalid base64 string: {e}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    return output_path


def get_pdf_page_count(pdf_path: str) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF

    Example:
        >>> pages = get_pdf_page_count("document.pdf")
        >>> print(f"Document has {pages} pages")
        'Document has 42 pages'
    """
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        raise ValueError(f"Invalid PDF file: {e}")


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in megabytes (rounded to 2 decimal places)

    Raises:
        FileNotFoundError: If file doesn't exist

    Example:
        >>> size = get_file_size_mb("document.pdf")
        >>> print(f"File size: {size}MB")
        'File size: 2.45MB'
    """
    file = Path(file_path)

    if not file.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    size_bytes = file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    return round(size_mb, 2)


def validate_pdf_file(
    file_path: str,
    max_size_mb: Optional[int] = None,
    check_extension: bool = True
) -> bool:
    """
    Validate PDF file exists, has correct extension, and is within size limit.

    Args:
        file_path: Path to the PDF file
        max_size_mb: Maximum allowed size in MB (default: from constants)
        check_extension: Whether to validate file extension

    Returns:
        True if file is valid

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file extension is invalid or file is too large

    Example:
        >>> validate_pdf_file("document.pdf", max_size_mb=10)
        True
        >>> validate_pdf_file("large_file.pdf", max_size_mb=1)
        ValueError: PDF too large: 2.5MB > 1MB
    """
    file = Path(file_path)

    # Check existence
    if not file.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    # Check extension
    if check_extension and file.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file extension: {file.suffix}. "
            f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check size
    max_size = max_size_mb if max_size_mb is not None else MAX_FILE_SIZE_MB
    size_mb = get_file_size_mb(file_path)

    if size_mb > max_size:
        raise ValueError(f"PDF too large: {size_mb}MB > {max_size}MB")

    return True


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename by removing unsafe characters.

    Args:
        filename: Original filename
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename

    Example:
        >>> sanitize_filename("my/file:name?.pdf")
        'my_file_name_.pdf'
    """
    # Replace unsafe characters
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename

    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')

    # Limit length
    if len(sanitized) > max_length:
        name, ext = Path(sanitized).stem, Path(sanitized).suffix
        max_name_length = max_length - len(ext)
        sanitized = name[:max_name_length] + ext

    return sanitized


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "2.5 MB")

    Example:
        >>> format_file_size(2621440)
        '2.50 MB'
        >>> format_file_size(1024)
        '1.00 KB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.2f} PB"
