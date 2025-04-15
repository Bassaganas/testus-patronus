from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from typing import List, Optional

from app.domain.schemas.document import DocumentResponse, DocumentSourceConfig, DocumentUpdate
from app.application.services.document_service import DocumentService
from app.api.container import get_document_service
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="Get All Documents",
    description="Retrieve a list of all documents, optionally filtered by project or conversation"
)
async def get_documents(
    project_id: Optional[str] = Query(None, description="Filter documents by project ID"),
    conversation_id: Optional[str] = Query(None, description="Filter documents by conversation ID"),
    service: DocumentService = Depends(get_document_service)
):
    """Get all documents, optionally filtered by project or conversation."""
    return await service.get_documents(project_id, conversation_id)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get Document",
    description="Retrieve a specific document by ID"
)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Get a specific document."""
    return await service.get_document(document_id)

@router.post(
    "/upload",
    response_model=DocumentResponse,
    summary="Upload Document",
    description="Upload and process a new document, associating it with a project and optionally a conversation"
)
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Query(None, description="Project ID to associate the document with"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID to explicitly associate the document with"),
    service: DocumentService = Depends(get_document_service)
):
    """
    Upload and process a new document.
    
    Documents can be:
    - Associated with a project (recommended)
    - Explicitly associated with a conversation (optional)
    
    Documents associated with a project will be available for queries from all conversations in that project.
    Documents explicitly associated with a conversation will be prioritized in that conversation's queries.
    """
    return await service.upload_document(file, project_id, conversation_id)

@router.post(
    "/import",
    response_model=DocumentResponse,
    summary="Import Document",
    description="Import a document from an external source (Confluence, Jira, GitHub, etc.)"
)
async def import_document(
    source_config: DocumentSourceConfig,
    source_id: str,
    project_id: Optional[str] = Query(None, description="Project ID to associate the document with"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID to associate the document with"),
    service: DocumentService = Depends(get_document_service)
):
    """Import a document from an external source."""
    return await service.import_from_source(
        source_config.source_type,
        source_id,
        project_id,
        conversation_id
    )

@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Update Document",
    description="Update an existing document's metadata"
)
async def update_document(
    document_id: str,
    document: DocumentUpdate,
    service: DocumentService = Depends(get_document_service)
):
    """Update a document."""
    return await service.update_document(document_id, document)

@router.delete(
    "/{document_id}",
    summary="Delete Document",
    description="Delete a document and its associated vectors"
)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    """Delete a document."""
    await service.delete_document(document_id)
    return {"message": "Document deleted successfully"} 