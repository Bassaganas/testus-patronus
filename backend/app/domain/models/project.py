from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

class Project:
    """
    Domain model for Project
    """
    def __init__(
        self,
        id: Optional[UUID] = None,
        title: str = "",
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        documents: Optional[List[UUID]] = None,
        conversations: Optional[List[UUID]] = None
    ):
        self.id = id or uuid4()
        self.title = title
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.documents = documents or []
        self.conversations = conversations or []
    
    def update(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        Update project attributes
        """
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        self.updated_at = datetime.now() 