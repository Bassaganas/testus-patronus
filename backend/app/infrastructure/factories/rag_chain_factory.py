from app.infrastructure.rag.rag_chain import RAGChain
from .vector_store_factory import VectorStoreFactory

class RAGChainFactory:
    _instance = None

    @classmethod
    def get_rag_chain(cls):
        if cls._instance is None:
            vector_store = VectorStoreFactory.get_vector_store()
            cls._instance = RAGChain(vector_store)
        return cls._instance 