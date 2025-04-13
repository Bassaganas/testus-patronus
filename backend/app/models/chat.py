from .base import BaseModel, Optional, List
from .conversation import Message

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    user_message: Optional[Message] = None
    assistant_message: Optional[Message] = None
    sources: Optional[List[str]] = [] 