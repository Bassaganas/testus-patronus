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
    return await document_service.get_documents(project_id, conversation_id)

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
    return await document_service.get_document(document_id)

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
    """Update a document's metadata."""
    return await document_service.update_document(document_id, document)

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