from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from typing import List, Optional

from app.domain.schemas.document import DocumentResponse, DocumentSourceConfig, DocumentUpdate
from app.application.services.document_service import DocumentService
from app.api.container import get_document_service
from app.core.exceptions import NotFoundException, ValidationException
from app.infrastructure.vector_store.vector_store import VectorStoreManager

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

@router.get(
    "/{document_id}/vector",
    summary="Check Document in Vector Store",
    description="Check if a document exists in the vector store and return its contents"
)
async def check_document_in_vector_store(
    document_id: str,
    vector_store: VectorStoreManager = Depends(VectorStoreManager)
):
    """Check if a document exists in the vector store and return its contents."""
    try:
        documents = vector_store.get_document(document_id)
        if not documents:
            raise HTTPException(status_code=404, detail="Document not found in vector store")
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in documents]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get(
    "/vector/check",
    summary="Check Documents in Vector Store",
    description="Check documents in the vector store for a specific project or conversation"
)
async def check_documents_in_vector_store(
    project_id: Optional[str] = Query(None, description="Filter documents by project ID"),
    conversation_id: Optional[str] = Query(None, description="Filter documents by conversation ID"),
    limit: int = Query(5, description="Maximum number of documents to return"),
    vector_store: VectorStoreManager = Depends(VectorStoreManager)
):
    """Check documents in the vector store for a specific project or conversation."""
    try:
        # Build filter dictionary
        filter_dict = {}
        if project_id:
            filter_dict["project_id"] = project_id
        if conversation_id:
            filter_dict["conversation_id"] = conversation_id
            
        # If no filters, return a message
        if not filter_dict:
            return {"message": "Please provide project_id or conversation_id to filter documents"}
            
        # Perform a search with a generic query to get documents
        results = vector_store._execute_search(
            query="Find all documents", 
            k=limit, 
            filter_dict=filter_dict, 
            score_threshold=0.0
        )
        
        if not results:
            return {"message": f"No documents found in vector store with the specified filters"}
            
        # Format the results
        formatted_results = []
        for i, doc in enumerate(results):
            # Get a preview of the content
            content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            
            result = {
                "index": i+1,
                "document_id": doc.metadata.get("document_id", "Unknown"),
                "source_type": doc.metadata.get("source_type", "Unknown"),
                "content_preview": content_preview,
                "metadata": doc.metadata
            }
            
            # Add Jira-specific fields if available
            if doc.metadata.get("source_type") == "jira":
                result["issue_key"] = doc.metadata.get("issue_key", "Unknown")
                result["issue_type"] = doc.metadata.get("issue_type", "Unknown")
                result["status"] = doc.metadata.get("status", "Unknown")
                
            formatted_results.append(result)
            
        return {
            "count": len(results),
            "documents": formatted_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 