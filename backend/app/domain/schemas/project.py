from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from typing import List, Optional, Annotated
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    """
    Base schema for Project
    """
    title: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    description: Optional[Annotated[str, StringConstraints(max_length=1000)]] = None

class ProjectCreate(ProjectBase):
    """
    Schema for creating a Project
    """
    id: Optional[str | UUID] = None

class ProjectUpdate(ProjectBase):
    """
    Schema for updating a Project
    """
    pass

class ProjectResponse(ProjectBase):
    """
    Schema for Project response
    """
    id: str | UUID
    created_at: datetime
    updated_at: datetime
    documents: List[str | UUID] = Field(default_factory=list)
    conversations: List[str | UUID] = Field(default_factory=list)

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