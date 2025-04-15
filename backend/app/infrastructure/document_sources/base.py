from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from fastapi import UploadFile
from pydantic import BaseModel

class DocumentData(BaseModel):
    """Data structure for processed documents."""
    title: str
    content: str
    metadata: Dict[str, Any] = {}

class DocumentSource(ABC):
    """Base class for document sources."""
    
    @abstractmethod
    async def process_upload(self, file: UploadFile) -> DocumentData:
        """Process an uploaded file."""
        pass
    
    @abstractmethod
    async def process_document(self, source_id: str) -> DocumentData:
        """Process a document from the source system."""
        pass
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate the source credentials."""
        pass 