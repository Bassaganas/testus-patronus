from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from app.infrastructure.database.models.document import Document
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.core.exceptions import NotFoundException

class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all(self, project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> List[Document]:
        query = select(Document)
        if project_id:
            query = query.where(Document.project_id == project_id)
        if conversation_id:
            query = query.join(Document.conversations).where(Document.conversations.any(id=conversation_id))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_id(self, document_id: str) -> Document:
        query = select(Document).where(Document.id == document_id)
        result = await self.db.execute(query)
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundException(f"Document with id {document_id} not found")
        return document
    
    async def get_by_conversation(self, conversation_id: str) -> List[Document]:
        """Get all documents for a conversation."""
        query = select(Document).join(Document.conversations).where(Document.conversations.any(id=conversation_id))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_project(self, project_id: str) -> List[Document]:
        """Get all documents for a project."""
        query = select(Document).where(Document.project_id == project_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_source(self, source_type: str, source_id: str) -> Optional[Document]:
        """Get a document by its source type and ID."""
        query = select(Document).where(
            Document.source_type == source_type,
            Document.source_id == source_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, document: DocumentCreate) -> Document:
        db_document = Document(
            title=document.title,
            source_type=document.source_type,
            source_id=document.source_id,
            file_name=document.file_name,
            file_type=document.file_type,
            file_size=document.file_size,
            content=document.content,
            doc_metadata=document.doc_metadata,
            project_id=document.project_id
        )
        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)
        return db_document
    
    async def update(self, document_id: str, document: DocumentUpdate) -> Document:
        db_document = await self.get_by_id(document_id)
        
        update_data = document.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_document, key, value)
        
        await self.db.commit()
        await self.db.refresh(db_document)
        return db_document
    
    async def delete(self, document_id: str) -> None:
        document = await self.get_by_id(document_id)
        await self.db.delete(document)
        await self.db.commit()
    
    async def delete_by_conversation(self, conversation_id: str) -> None:
        """Delete all documents for a conversation."""
        documents = await self.get_by_conversation(conversation_id)
        for doc in documents:
            doc.conversations = [c for c in doc.conversations if c.id != conversation_id]
        await self.db.commit()
    
    async def delete_by_project(self, project_id: str) -> None:
        """Delete all documents for a project."""
        query = select(Document).where(Document.project_id == project_id)
        result = await self.db.execute(query)
        documents = result.scalars().all()
        for doc in documents:
            await self.db.delete(doc)
        await self.db.commit() 