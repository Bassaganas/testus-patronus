from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from typing import List, Optional, Annotated, Dict, Any
from datetime import datetime
from uuid import UUID

class MessageBase(BaseModel):
    """
    Base schema for Message
    """
    role: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    content: Annotated[str, StringConstraints(min_length=1, max_length=10000)]

class MessageResponse(MessageBase):
    """
    Schema for Message response
    """
    id: str
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "user",
                "content": "Hello, how can you help me?",
                "timestamp": "2024-01-01T00:00:00"
            }
        }
    )

class ConversationBase(BaseModel):
    """
    Base schema for Conversation
    """
    title: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    project_id: Optional[str] = None

class ConversationCreate(ConversationBase):
    """
    Schema for creating a Conversation
    """
    pass

class ConversationUpdate(ConversationBase):
    """
    Schema for updating a Conversation
    """
    title: Optional[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = None
    project_id: Optional[str] = None

class ConversationResponse(ConversationBase):
    """
    Schema for Conversation response
    """
    id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "My Conversation",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "messages": [],
                "documents": []
            }
        }
    )

class QueryResponse(BaseModel):
    """
    Schema for query response
    """
    response: str
    conversation_id: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "response": "This is a response to your query.",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    ) 