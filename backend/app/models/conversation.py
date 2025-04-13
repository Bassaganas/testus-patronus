from .base import BaseModel, Field, Optional, List, uuid4, datetime

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    messages: List[Message] = []
    documents: List[str] = []  # Document IDs

class ConversationCreate(BaseModel):
    title: str
    project_id: Optional[str] = None 