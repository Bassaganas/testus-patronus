from app.infrastructure.vector_store.vector_store import VectorStoreManager
from functools import lru_cache

@lru_cache()
def get_vector_store() -> VectorStoreManager:
    """
    Get or create a VectorStoreManager instance.
    Uses lru_cache to maintain a single instance.
    
    Returns:
        VectorStoreManager: The vector store manager instance
    """
    return VectorStoreManager() 