"""
Health Check Routes.

Provides system health status and client connectivity checks.
"""

import logging
from fastapi import APIRouter

from src.api.models import HealthResponse, WorkflowListResponse
from src.services.client_factory import get_client_factory
from src.services.workflow_router import list_available_workflows
from src.core.security import get_api_key_status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns service status and AI client connectivity.

    Returns:
        HealthResponse with status and client information
    """
    logger.info("Health check requested")

    try:
        # Get client factory
        factory = get_client_factory()

        # Check all clients
        clients_status = await factory.health_check_all()

        # Determine overall status
        all_healthy = all(
            client.get("status") == "ok" for client in clients_status.values()
        )
        status = "healthy" if all_healthy else "degraded"

        return HealthResponse(status=status, version="1.0.0", clients=clients_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            clients={"error": {"status": "error", "message": str(e)}},
        )


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows():
    """List available extraction workflows.

    Returns:
        WorkflowListResponse with workflow names and descriptions
    """
    logger.info("Workflows list requested")

    workflows = list_available_workflows()

    return WorkflowListResponse(workflows=workflows)


@router.get("/status")
async def service_status():
    """Get detailed service status.

    Returns:
        Dictionary with service configuration and status
    """
    logger.info("Service status requested")

    return {
        "service": "Blackedge-OCR",
        "version": "1.0.0",
        "status": "running",
        "authentication": get_api_key_status(),
        "features": {
            "validation": True,
            "workflows": 5,
            "ai_providers": 4,
        },
    }
