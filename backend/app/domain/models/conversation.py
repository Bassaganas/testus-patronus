from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

class Message:
    """
    Domain model for Message
    """
    def __init__(
        self,
        id: Optional[UUID] = None,
        role: str = "",
        content: str = "",
        timestamp: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()

class Conversation:
    """
    Domain model for Conversation
    """
    def __init__(
        self,
        id: Optional[UUID] = None,
        title: str = "",
        project_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        messages: Optional[List[Message]] = None,
        documents: Optional[List[UUID]] = None
    ):
        self.id = id or uuid4()
        self.title = title
        self.project_id = project_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.messages = messages or []
        self.documents = documents or []
    
    def add_message(self, role: str, content: str) -> Message:
        """
        Add a message to the conversation
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def add_document(self, document_id: UUID) -> None:
        """
        Add a document to the conversation
        """
        if document_id not in self.documents:
            self.documents.append(document_id)
            self.updated_at = datetime.now()
    
    def remove_document(self, document_id: UUID) -> None:
        """
        Remove a document from the conversation
        """
        if document_id in self.documents:
            self.documents.remove(document_id)
            self.updated_at = datetime.now()
    
    def update(self, title: Optional[str] = None) -> None:
        """
        Update conversation attributes
        """
        if title is not None:
            self.title = title
        self.updated_at = datetime.now() 