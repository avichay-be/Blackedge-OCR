"""
Main FastAPI Application.

Entry point for the Blackedge-OCR API server.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routes import extraction, health
from src.core.config import settings

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Blackedge-OCR API",
    description="Multi-strategy PDF extraction with AI validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(
    extraction.router,
    prefix="/api/v1",
    tags=["extraction"],
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"],
)


@app.get("/")
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Blackedge-OCR API server")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Key Required: {bool(settings.API_KEY)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Blackedge-OCR API server")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
