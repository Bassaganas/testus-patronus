from fastapi import APIRouter
from app.api.v1.endpoints import projects, conversations, documents, health

# Create the main v1 router
router = APIRouter(prefix="/api/v1")

# Include all route modules
router.include_router(health.router)
router.include_router(projects.router)
router.include_router(conversations.router)
router.include_router(documents.router)

# Root endpoint for API v1
@router.get("/", tags=["Root"])
async def api_root():
    """
    Root endpoint for API v1.
    Returns basic API information.
    """
    return {
        "name": "Testus Patronus API",
        "version": "1.0.0",
        "status": "operational"
    } 