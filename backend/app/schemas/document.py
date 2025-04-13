from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime

class DocumentBase(BaseModel):
    """Base schema for document data."""
    title: str
    file_name: str
    file_type: str
    file_size: float
    content: Optional[str] = None
    metadata: Optional[Dict] = Field(default_factory=dict)
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass

class DocumentUpdate(DocumentBase):
    """Schema for updating an existing document."""
    title: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[float] = None
    content: Optional[str] = None
    metadata: Optional[Dict] = None
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None

class DocumentResponse(DocumentBase):
    """Schema for document response data."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 