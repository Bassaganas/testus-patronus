from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Integer, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.infrastructure.database.base import Base

# Association table for many-to-many relationship between documents and conversations
document_conversation = Table(
    "document_conversation",
    Base.metadata,
    Column("document_id", String, ForeignKey("documents.id"), primary_key=True),
    Column("conversation_id", String, ForeignKey("conversations.id"), primary_key=True)
)

class Document(Base):
    """
    Database model for Document
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True, default={})
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="documents")
    conversations = relationship("Conversation", secondary=document_conversation, back_populates="documents") 