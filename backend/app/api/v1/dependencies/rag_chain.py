from app.rag_chain import RAGChain
from app.api.v1.dependencies.vector_store import get_vector_store
from functools import lru_cache

@lru_cache()
def get_rag_chain() -> RAGChain:
    """
    Get or create a RAGChain instance.
    Uses lru_cache to maintain a single instance.
    
    Returns:
        RAGChain: The RAG chain instance
    """
    vector_store = get_vector_store()
    return RAGChain(vector_store) 