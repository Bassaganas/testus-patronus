from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    """Base schema for document data."""
    title: str
    source_type: str
    source_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    content: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""
    title: Optional[str] = None
    content: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None

class DocumentResponse(DocumentBase):
    """Schema for document response data."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentSourceConfig(BaseModel):
    """Configuration for different document sources."""
    source_type: str
    credentials: Dict[str, Any]
    settings: Dict[str, Any] = Field(default_factory=dict) 