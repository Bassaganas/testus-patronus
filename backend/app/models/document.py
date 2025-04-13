from .base import BaseModel, Field, Optional, Dict, Any, uuid4, datetime

class DocumentMetadata(BaseModel):
    """Metadata for a document."""
    title: Optional[str] = None
    author: Optional[str] = None
    format: Optional[str] = None
    page_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    slide_count: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    extra: Dict[str, Any] = {}

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    content: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None

class DocumentCreate(BaseModel):
    title: str
    file_name: str
    file_type: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = {}
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None 