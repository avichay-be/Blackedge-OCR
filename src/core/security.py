"""
Security Module.

Provides API authentication and authorization.
"""

import logging
from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> bool:
    """Verify API key from Authorization header.

    Checks the Bearer token against the configured API key.
    If no API key is configured, allows all requests (open access).

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        True if authentication successful

    Raises:
        HTTPException: If API key is invalid (401)

    Examples:
        # In route:
        @router.get("/protected")
        async def protected_route(_: bool = Depends(verify_api_key)):
            return {"message": "Access granted"}

        # Request with API key:
        curl -H "Authorization: Bearer your-api-key" http://localhost:8000/protected
    """
    expected_key = settings.API_KEY

    # No API key configured - allow all requests
    if not expected_key:
        logger.debug("No API key configured, allowing access")
        return True

    # No credentials provided
    if not credentials:
        logger.warning("API key required but not provided")
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide Authorization: Bearer <token> header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify API key
    provided_key = credentials.credentials

    if provided_key != expected_key:
        logger.warning(f"Invalid API key provided: {provided_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("API key verified successfully")
    return True


def get_api_key_status() -> dict:
    """Get API key configuration status.

    Returns:
        Dictionary with API key status information
    """
    return {
        "api_key_required": bool(settings.API_KEY),
        "api_key_configured": bool(settings.API_KEY),
    }
