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
        
        print(f"Upload document - Project ID: {project_id}, Conversation ID: {conversation_id}")
        
        # Create document
        document_create = DocumentCreate(
            title=document_data.title,
            source_type="file",
            file_name=file.filename,
            file_type=file.content_type,
            file_size=document_data.metadata.get("file_size"),
            content=document_data.content,
            doc_metadata=document_data.metadata,
            project_id=project_id,
            conversation_id=conversation_id
        )
        
        # Save to database
        document = await self.repository.create(document_create)
        
        print(f"Created document in DB: ID={document.id}, Type={type(document.id)}")
        
        # If conversation_id is provided, associate the document with the conversation
        if conversation_id:
            from app.infrastructure.repositories.conversation_repository import ConversationRepository
            conversation_repo = ConversationRepository(self.repository.db)
            try:
                await conversation_repo.add_document(conversation_id, document.id)
                print(f"Associated document {document.id} with conversation {conversation_id}")
            except Exception as e:
                print(f"Error associating document with conversation: {e}")
        
        # Add to vector store
        if document.content:
            # Merge all metadata for the vector store
            vector_metadata = dict(document_data.metadata) if document_data.metadata else {}
            
            # Convert all IDs to strings to ensure consistency
            document_id_str = str(document.id)
            project_id_str = str(project_id) if project_id else None
            conversation_id_str = str(conversation_id) if conversation_id else None
            
            vector_metadata["document_id"] = document_id_str
            if project_id_str:
                vector_metadata["project_id"] = project_id_str
            if conversation_id_str:
                vector_metadata["conversation_id"] = conversation_id_str
                
            print(f"Adding document to vector store with metadata: {vector_metadata}")
            
            # Add document to vector store
            self.vector_store.add_documents(
                [{"page_content": document.content, "metadata": vector_metadata}],
                document_id=document_id_str,
                project_id=project_id_str,
                conversation_id=conversation_id_str
            )
            
            # Verify document was added to vector store
            try:
                docs = self.vector_store.get_document(document_id_str)
                print(f"Retrieved {len(docs)} chunks for document {document_id_str} from vector store")
            except Exception as e:
                print(f"Error verifying document in vector store: {e}")
        
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
            doc_metadata=document_data.metadata,
            project_id=project_id,
            conversation_id=conversation_id
        )
        
        # Save to database
        document = await self.repository.create(document_create)
        
        # If conversation_id is provided, associate the document with the conversation
        if conversation_id:
            from app.infrastructure.repositories.conversation_repository import ConversationRepository
            conversation_repo = ConversationRepository(self.repository.db)
            try:
                await conversation_repo.add_document(conversation_id, document.id)
            except Exception as e:
                print(f"Error associating document with conversation: {e}")
        
        # Add to vector store
        if document.content:
            # Create metadata for vector store
            vector_metadata = {"document_id": str(document.id)}
            if project_id:
                vector_metadata["project_id"] = str(project_id)
            if conversation_id:
                vector_metadata["conversation_id"] = str(conversation_id)
                
            self.vector_store.add_documents(
                [{"page_content": document.content, "metadata": vector_metadata}],
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
        
        # Check if conversation_id is being updated
        new_conversation_id = document_update.conversation_id
        if new_conversation_id and new_conversation_id != existing_document.conversation_id:
            # First, update the database record
            updated_document = await self.repository.update(document_id, document_update)
            
            # Then, update the many-to-many relationship
            from app.infrastructure.repositories.conversation_repository import ConversationRepository
            conversation_repo = ConversationRepository(self.repository.db)
            try:
                # Add to new conversation if specified
                await conversation_repo.add_document(new_conversation_id, document_id)
            except Exception as e:
                print(f"Error updating document's conversation: {e}")
        else:
            # Regular update without conversation changes
            updated_document = await self.repository.update(document_id, document_update)
        
        # Update vector store if content changed
        if document_update.content and document_update.content != existing_document.content:
            # Create metadata for vector store
            vector_metadata = {"document_id": str(updated_document.id)}
            if updated_document.project_id:
                vector_metadata["project_id"] = str(updated_document.project_id)
            if updated_document.conversation_id:
                vector_metadata["conversation_id"] = str(updated_document.conversation_id)
                
            self.vector_store.add_documents(
                [{"page_content": updated_document.content, "metadata": vector_metadata}],
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