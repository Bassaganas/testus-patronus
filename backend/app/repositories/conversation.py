from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Conversation, Document
from app.models.conversation import Message
from datetime import datetime

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Conversation]:
        """Get all conversations."""
        return self.db.query(Conversation).all()
    
    def get_by_id(self, id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self.db.query(Conversation).filter(Conversation.id == id).first()
    
    def get_by_project(self, project_id: str) -> List[Conversation]:
        """Get all conversations for a project."""
        return self.db.query(Conversation).filter(Conversation.project_id == project_id).all()
    
    def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        # Ensure timestamps are set
        if not conversation.created_at:
            conversation.created_at = datetime.utcnow()
        if not conversation.updated_at:
            conversation.updated_at = datetime.utcnow()
            
        # Initialize empty lists
        if not conversation.messages:
            conversation.messages = []
            
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def update(self, id: str, conversation: Conversation) -> Optional[Conversation]:
        """Update an existing conversation."""
        existing = self.get_by_id(id)
        if existing:
            # Update fields
            for key, value in conversation.__dict__.items():
                if not key.startswith('_') and hasattr(existing, key):
                    setattr(existing, key, value)
            
            # Update timestamp
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return None
    
    def delete(self, id: str) -> bool:
        """Delete a conversation."""
        conversation = self.get_by_id(id)
        if conversation:
            # Delete associated documents
            for document in conversation.documents:
                self.db.delete(document)
            
            # Delete the conversation
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False
    
    def add_message(self, conversation_id: str, message: Message) -> Optional[Conversation]:
        """Add a message to a conversation."""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            # Convert Message model to dict for JSON storage
            message_dict = {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            }
            
            if not conversation.messages:
                conversation.messages = []
            
            conversation.messages.append(message_dict)
            conversation.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        return None
    
    def add_document(self, conversation_id: str, document_id: str) -> Optional[Conversation]:
        """Add a document to a conversation."""
        conversation = self.get_by_id(conversation_id)
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if conversation and document:
            # Update document's conversation reference
            document.conversation_id = conversation_id
            document.conversation = conversation
            
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        return None
    
    def remove_document(self, conversation_id: str, document_id: str) -> Optional[Conversation]:
        """Remove a document from a conversation."""
        conversation = self.get_by_id(conversation_id)
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if conversation and document and document.conversation_id == conversation_id:
            # Remove document's conversation reference
            document.conversation_id = None
            document.conversation = None
            
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        return None 