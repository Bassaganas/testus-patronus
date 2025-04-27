from fastapi import Depends
from app.infrastructure.database.session import get_db
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.factories.vector_store_factory import VectorStoreFactory

async def get_vector_store_manager() -> VectorStoreManager:
    """
    Get a vector store manager instance.
    
    Returns:
        VectorStoreManager: A vector store manager instance
    """
    return VectorStoreFactory.get_vector_store() 