from fastapi import APIRouter, Depends
from app.infrastructure.vector_store.vector_store import VectorStoreManager

router = APIRouter(prefix="/health", tags=["Health"])

@router.get(
    "",
    summary="Health Check",
    description="Check the health of the API and its components"
)
async def health_check(
    vector_store: VectorStoreManager = Depends(VectorStoreManager)
):
    """
    Check the health of the API and its components.
    
    Args:
        vector_store: Vector store manager
        
    Returns:
        dict: Health status
    """
    try:
        # Test vector store
        vector_store.similarity_search("test", k=1)
        
        return {
            "status": "healthy",
            "components": {
                "vector_store": "operational"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 