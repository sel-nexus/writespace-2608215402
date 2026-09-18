"""Database-aware health route with a safe failure response."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.schemas import HealthResponse, HealthUnavailableResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=200,
    summary="Check database reachability",
    responses={503: {"model": HealthUnavailableResponse}},
)
def get_health(request: Request) -> HealthResponse | JSONResponse:
    """Probe SQLite with SELECT 1 and return a safe status response."""
    try:
        with request.app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return HealthResponse()
    except SQLAlchemyError:
        logger.warning("Database health probe failed")
        return JSONResponse(status_code=503, content=HealthUnavailableResponse().model_dump())
