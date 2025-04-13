from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4

class ConversationBase(BaseModel):
    """Base schema for conversation data."""
    title: str
    project_id: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    pass

class ConversationUpdate(ConversationBase):
    """Schema for updating an existing conversation."""
    title: Optional[str] = None
    project_id: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None

class ConversationResponse(ConversationBase):
    """Schema for conversation response data."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 