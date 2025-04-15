from app.infrastructure.document_sources.file_source import FileDocumentSource
from functools import lru_cache

@lru_cache()
def get_document_processor() -> FileDocumentSource:
    """
    Get or create a FileDocumentSource instance.
    Uses lru_cache to maintain a single instance.
    
    Returns:
        FileDocumentSource: The file document source instance
    """
    return FileDocumentSource() 