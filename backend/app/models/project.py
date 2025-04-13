from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from typing import List, Optional, Annotated
from datetime import datetime
from uuid import uuid4

class ProjectBase(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    description: Optional[Annotated[str, StringConstraints(max_length=1000)]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    documents: List[str] = Field(default_factory=list)  # Document IDs
    conversations: List[str] = Field(default_factory=list)  # Conversation IDs

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Sample Project",
                "description": "A sample project description",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "documents": [],
                "conversations": []
            }
        }
    ) 