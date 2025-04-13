from typing import List, Optional
from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.models import Document
from app.db.session import get_db
from app.vector_store import VectorStoreManager
from app.document_processor import DocumentProcessor
from datetime import datetime
import logging

logger = logging.getLogger("testus-patronus")

class DocumentService:
    def __init__(self, db: Session, vector_store: VectorStoreManager, doc_processor: DocumentProcessor):
        self.db = db
        self.vector_store = vector_store
        self.doc_processor = doc_processor
        
    async def get_documents(self, project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> List[Document]:
        """Get all documents, optionally filtered by project or conversation."""
        query = self.db.query(Document)
        if project_id:
            query = query.filter(Document.project_id == project_id)
        if conversation_id:
            query = query.filter(Document.conversation_id == conversation_id)
        return query.all()
        
    async def get_document(self, document_id: str) -> Document:
        """Get a specific document."""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        return document
        
    async def upload_document(
        self,
        file: UploadFile,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Document:
        """Upload and process a new document."""
        try:
            # Process document using document processor
            processed_doc = await self.doc_processor.process_document(
                file=file,
                vector_store=self.vector_store,
                conversation_id=conversation_id,
                project_id=project_id
            )
            
            # Create document in database
            self.db.add(processed_doc)
            self.db.commit()
            self.db.refresh(processed_doc)
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
            
    async def update_document(self, document_id: str, document: Document) -> Document:
        """Update a document's metadata."""
        db_document = await self.get_document(document_id)
        
        # Update fields
        for key, value in document.dict(exclude={'id'}).items():
            setattr(db_document, key, value)
        
        db_document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_document)
        
        # Update document vectors if necessary
        self.vector_store.update_document(db_document)
        
        return db_document
        
    async def delete_document(self, document_id: str) -> None:
        """Delete a document and its vectors."""
        document = await self.get_document(document_id)
        
        # Delete from vector store
        self.vector_store.delete_document(document_id)
        
        # Delete from database
        self.db.delete(document)
        self.db.commit() 