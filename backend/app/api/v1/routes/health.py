from fastapi import APIRouter, Depends
from typing import Dict
from pydantic import BaseModel
from app.api.v1.dependencies.service_check import check_services

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    """Response model for health check endpoints"""
    status: str
    components: Dict[str, str] = {}

class DetailedHealthResponse(HealthResponse):
    """Response model for detailed health check"""
    version: str
    uptime: float

@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic Health Check",
    description="Returns basic health status of the API"
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse: Basic health status
    """
    return HealthResponse(
        status="healthy",
        components={
            "api": "operational"
        }
    )

@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    summary="Detailed Health Check",
    description="Returns detailed health information including component status"
)
async def detailed_health_check(
    services: Dict[str, str] = Depends(check_services)
) -> DetailedHealthResponse:
    """
    Detailed health check endpoint that verifies all system components.
    
    Args:
        services: Dictionary of service statuses (injected by dependency)
    
    Returns:
        DetailedHealthResponse: Detailed health status including component states
    """
    from app.config import settings
    import psutil
    
    return DetailedHealthResponse(
        status="healthy",
        components=services,
        version=settings.API_VERSION,
        uptime=psutil.boot_time()
    ) 