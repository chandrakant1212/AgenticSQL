"""
Health check API endpoint.

GET /api/health — Application and database health check.
"""

import logging

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.database.connection import check_database_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check application and database health."""
    db_health = check_database_health()

    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "degraded",
        database=db_health["status"],
        message=db_health.get("message", ""),
        version="1.0.0",
    )
