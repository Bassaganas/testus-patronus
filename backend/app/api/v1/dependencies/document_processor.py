from app.document_processor import DocumentProcessor
from functools import lru_cache

@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """
    Get or create a DocumentProcessor instance.
    Uses lru_cache to maintain a single instance.
    
    Returns:
        DocumentProcessor: The document processor instance
    """
    return DocumentProcessor() 