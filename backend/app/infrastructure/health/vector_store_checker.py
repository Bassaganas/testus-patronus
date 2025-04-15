from app.infrastructure.vector_store.vector_store import VectorStoreManager

class VectorStoreHealthChecker:
    service_name = "vector_store"

    async def check_health(self) -> str:
        try:
            vector_store = VectorStoreManager()
            if vector_store.health_check():
                return "operational"
            return "degraded"
        except Exception:
            return "error" 