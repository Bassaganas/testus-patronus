from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import List, Optional
from app.models.document import Document
from app.services.document_service import DocumentService
from app.api.v1.dependencies.services import get_document_service
import logging

logger = logging.getLogger("testus-patronus")
router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get(
    "",
    response_model=List[Document],
    summary="Get All Documents",
    description="Retrieve a list of all documents, optionally filtered by project or conversation"
)
async def get_documents(
    project_id: Optional[str] = Query(None, description="Filter documents by project ID"),
    conversation_id: Optional[str] = Query(None, description="Filter documents by conversation ID"),
    document_service: DocumentService = Depends(get_document_service)
) -> List[Document]:
    """Get all documents, optionally filtered by project or conversation."""
    db_documents = await document_service.get_documents(project_id, conversation_id)
    
    # Convert SQLAlchemy models to Pydantic models
    documents = []
    for db_doc in db_documents:
        doc = Document(
            id=db_doc.id,
            title=db_doc.title,
            file_name=db_doc.file_name,
            file_type=db_doc.file_type,
            file_size=db_doc.file_size,
            content=db_doc.content,
            metadata=db_doc.doc_metadata,
            project_id=db_doc.project_id,
            conversation_id=db_doc.conversation_id,
            created_at=db_doc.created_at,
            updated_at=db_doc.updated_at
        )
        documents.append(doc)
    
    return documents

@router.get(
    "/{document_id}",
    response_model=Document,
    summary="Get Document",
    description="Retrieve a specific document by ID"
)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
) -> Document:
    """Get a specific document."""
    db_document = await document_service.get_document(document_id)
    
    # Convert SQLAlchemy model to Pydantic model
    doc = Document(
        id=db_document.id,
        title=db_document.title,
        file_name=db_document.file_name,
        file_type=db_document.file_type,
        file_size=db_document.file_size,
        content=db_document.content,
        metadata=db_document.doc_metadata,
        project_id=db_document.project_id,
        conversation_id=db_document.conversation_id,
        created_at=db_document.created_at,
        updated_at=db_document.updated_at
    )
    
    return doc

@router.post(
    "/upload",
    response_model=Document,
    summary="Upload Document",
    description="Upload and process a new document"
)
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Query(None, description="Project ID to associate the document with"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID to associate the document with"),
    document_service: DocumentService = Depends(get_document_service)
) -> Document:
    """Upload and process a new document."""
    return await document_service.upload_document(file, project_id, conversation_id)

@router.put(
    "/{document_id}",
    response_model=Document,
    summary="Update Document",
    description="Update an existing document's metadata"
)
async def update_document(
    document_id: str,
    document: Document,
    document_service: DocumentService = Depends(get_document_service)
) -> Document:
    """Update a document."""
    updated_doc = await document_service.update_document(document_id, document)
    
    # Convert SQLAlchemy model to Pydantic model
    doc = Document(
        id=updated_doc.id,
        title=updated_doc.title,
        file_name=updated_doc.file_name,
        file_type=updated_doc.file_type,
        file_size=updated_doc.file_size,
        content=updated_doc.content,
        metadata=updated_doc.doc_metadata,
        project_id=updated_doc.project_id,
        conversation_id=updated_doc.conversation_id,
        created_at=updated_doc.created_at,
        updated_at=updated_doc.updated_at
    )
    
    return doc

@router.delete(
    "/{document_id}",
    summary="Delete Document",
    description="Delete a document and its associated vectors"
)
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
):
    """Delete a document and its vectors."""
    await document_service.delete_document(document_id)
    return {"message": "Document deleted successfully"} 