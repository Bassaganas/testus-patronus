from typing import Dict
import httpx
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.core.config import settings

async def check_services() -> Dict[str, str]:
    """
    Check the health of all dependent services.
    
    Returns:
        Dict[str, str]: Dictionary of service names and their status
    """
    services = {
        "api": "operational",
        "vector_store": "unknown",
        "openai": "unknown"
    }
    
    # Check Vector Store
    try:
        vector_store = VectorStoreManager()
        # Add a simple health check method to your VectorStoreManager
        if vector_store.health_check():
            services["vector_store"] = "operational"
        else:
            services["vector_store"] = "degraded"
    except Exception:
        services["vector_store"] = "error"
    
    # Check OpenAI (simple connectivity check)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments",
                headers={
                    "api-key": settings.AZURE_OPENAI_API_KEY,
                    "api-version": settings.AZURE_OPENAI_API_VERSION
                },
                timeout=5.0
            )
            if response.status_code == 200:
                services["openai"] = "operational"
            else:
                services["openai"] = "degraded"
    except Exception:
        services["openai"] = "error"
    
    return services 