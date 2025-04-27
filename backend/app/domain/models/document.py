from typing import Optional, Dict, Any, List

class ContentPart:
    """
    Represents a part of a document's content with its associated metadata
    """
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.metadata = metadata or {}

class DocumentData:
    """
    Data class for document content and metadata
    """
    def __init__(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        content_parts: Optional[List[Dict[str, Any]]] = None
    ):
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        self.content_parts = content_parts or [] 