from typing import List, Optional, Dict, Any
from fastapi import UploadFile

from app.domain.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.core.exceptions import NotFoundException, ValidationException

class DocumentService:
    """
    Service for document operations
    """
    def __init__(
        self,
        repository: DocumentRepository,
        vector_store: VectorStoreManager,
        document_sources: Dict[str, Any]
    ):
        self.repository = repository
        self.vector_store = vector_store
        self.document_sources = document_sources

    async def get_documents(
        self, 
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> List[DocumentResponse]:
        """
        Get all documents, optionally filtered by project or conversation
        """
        return await self.repository.get_all(project_id, conversation_id)

    async def get_document(self, document_id: str) -> DocumentResponse:
        """
        Get a document by ID
        """
        document = await self.repository.get_by_id(document_id)
        if not document:
            raise NotFoundException(f"Document with ID {document_id} not found")
        return document

    async def upload_document(
        self,
        file: UploadFile,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> DocumentResponse:
        """
        Upload and process a new document
        """
        # Process the file using the file document source
        file_processor = self.document_sources.get("file")
        if not file_processor:
            raise ValidationException("File document processor not available")
            
        # Process the file
        document_data = await file_processor.process_upload(file)
        
        # Create document
        document_create = DocumentCreate(
            title=document_data.title,
            source_type="file",
            file_name=file.filename,
            file_type=file.content_type,
            file_size=document_data.metadata.get("file_size"),
            content=document_data.content,
            metadata=document_data.metadata,
            project_id=project_id,
            conversation_id=conversation_id
        )
        
        # Save to database
        document = await self.repository.create(document_create)
        
        # Add to vector store
        if document.content:
            self.vector_store.add_documents(
                [{"content": document.content, "metadata": {"document_id": str(document.id)}}],
                document_id=str(document.id),
                project_id=str(project_id) if project_id else None,
                conversation_id=str(conversation_id) if conversation_id else None
            )
        
        return document

    async def import_from_source(
        self,
        source_type: str,
        source_id: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> DocumentResponse:
        """
        Import a document from an external source
        """
        # Get the appropriate document source
        source_processor = self.document_sources.get(source_type)
        if not source_processor:
            raise ValidationException(f"Document source type '{source_type}' not available")
            
        # Process the document
        document_data = await source_processor.process_document(source_id)
        
        # Create document
        document_create = DocumentCreate(
            title=document_data.title,
            source_type=source_type,
            source_id=source_id,
            content=document_data.content,
            metadata=document_data.metadata,
            project_id=project_id,
            conversation_id=conversation_id
        )
        
        # Save to database
        document = await self.repository.create(document_create)
        
        # Add to vector store
        if document.content:
            self.vector_store.add_documents(
                [{"content": document.content, "metadata": {"document_id": str(document.id)}}],
                document_id=str(document.id),
                project_id=str(project_id) if project_id else None,
                conversation_id=str(conversation_id) if conversation_id else None
            )
        
        return document

    async def update_document(
        self,
        document_id: str,
        document_update: DocumentUpdate
    ) -> DocumentResponse:
        """
        Update a document
        """
        # Check if document exists
        existing_document = await self.get_document(document_id)
        
        # Update document
        updated_document = await self.repository.update(document_id, document_update)
        
        # Update vector store if content changed
        if document_update.content and document_update.content != existing_document.content:
            self.vector_store.add_documents(
                [{"content": updated_document.content, "metadata": {"document_id": str(updated_document.id)}}],
                document_id=str(updated_document.id),
                project_id=str(updated_document.project_id) if updated_document.project_id else None,
                conversation_id=str(updated_document.conversation_id) if updated_document.conversation_id else None
            )
        
        return updated_document

    async def delete_document(self, document_id: str) -> None:
        """
        Delete a document
        """
        # Check if document exists
        document = await self.get_document(document_id)
        
        # Delete from vector store
        self.vector_store.delete_document(str(document_id))
        
        # Delete from database
        await self.repository.delete(document_id) 