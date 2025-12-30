"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, datasets, health, ingest
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Ondo API",
    description="Dataset readiness scoring API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(ingest.router)
if settings.ai_assist_enabled:
    app.include_router(ai.router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "Ondo API",
        "version": "1.0.0",
        "docs": "/docs",
    }

