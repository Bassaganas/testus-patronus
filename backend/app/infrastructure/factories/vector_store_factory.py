from app.infrastructure.vector_store.vector_store import VectorStoreManager

class VectorStoreFactory:
    _instance = None

    @classmethod
    def get_vector_store(cls):
        if cls._instance is None:
            cls._instance = VectorStoreManager()
        return cls._instance 