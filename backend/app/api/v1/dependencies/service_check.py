from typing import Dict
import httpx
from app.vector_store import VectorStoreManager
from app.config import settings

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
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=5.0
            )
            if response.status_code == 200:
                services["openai"] = "operational"
            else:
                services["openai"] = "degraded"
    except Exception:
        services["openai"] = "error"
    
    return services 