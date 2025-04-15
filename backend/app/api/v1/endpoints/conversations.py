from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.domain.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse
from app.application.services.conversation_service import ConversationService
from app.infrastructure.database.session import get_db
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.rag.rag_chain import RAGChain, get_rag_chain
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/conversations", tags=["Conversations"])

async def get_conversation_service(
    db = Depends(get_db),
    vector_store: VectorStoreManager = Depends(VectorStoreManager),
    rag_chain: RAGChain = Depends(get_rag_chain)
) -> ConversationService:
    """
    Get conversation service
    """
    repository = ConversationRepository(db)
    return ConversationService(repository, vector_store, rag_chain)

@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="Get All Conversations",
    description="Retrieve a list of all conversations, optionally filtered by project_id"
)
async def get_conversations(
    project_id: Optional[str] = Query(None, description="Filter conversations by project ID"),
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Get all conversations.
    
    Args:
        project_id: Optional project ID to filter conversations
        service: Conversation service
        
    Returns:
        List[ConversationResponse]: List of all conversations
    """
    return await service.get_all_conversations(project_id)

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get Conversation by ID",
    description="Retrieve a specific conversation by its ID"
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Get a conversation by ID.
    
    Args:
        conversation_id: Conversation ID
        service: Conversation service
        
    Returns:
        ConversationResponse: Conversation details
        
    Raises:
        NotFoundException: If conversation not found
    """
    try:
        return await service.get_conversation_by_id(conversation_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "",
    response_model=ConversationResponse,
    summary="Create Conversation",
    description="Create a new conversation"
)
async def create_conversation(
    conversation: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Create a new conversation.
    
    Args:
        conversation: Conversation data
        service: Conversation service
        
    Returns:
        ConversationResponse: Created conversation
        
    Raises:
        ValidationException: If conversation data is invalid
    """
    try:
        return await service.create_conversation(conversation)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update Conversation",
    description="Update an existing conversation"
)
async def update_conversation(
    conversation_id: UUID,
    conversation: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Update a conversation.
    
    Args:
        conversation_id: Conversation ID
        conversation: Conversation data
        service: Conversation service
        
    Returns:
        ConversationResponse: Updated conversation
        
    Raises:
        NotFoundException: If conversation not found
        ValidationException: If conversation data is invalid
    """
    try:
        return await service.update_conversation(conversation_id, conversation)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Delete Conversation",
    description="Delete a conversation and its associated data"
)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        service: Conversation service
        
    Returns:
        ConversationResponse: Deleted conversation
        
    Raises:
        NotFoundException: If conversation not found
    """
    try:
        await service.delete_conversation(conversation_id)
        return {"message": f"Conversation {conversation_id} deleted successfully"}
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationResponse,
    summary="Add Message to Conversation",
    description="Add a new message to a conversation"
)
async def add_message(
    conversation_id: UUID,
    role: str,
    content: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: Conversation ID
        role: Message role (user or assistant)
        content: Message content
        service: Conversation service
        
    Returns:
        ConversationResponse: Updated conversation
        
    Raises:
        NotFoundException: If conversation not found
    """
    try:
        return await service.add_message(conversation_id, role, content)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/{conversation_id}/documents/{document_id}",
    response_model=ConversationResponse,
    summary="Add Document to Conversation",
    description="Add a document to a conversation"
)
async def add_document(
    conversation_id: UUID,
    document_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Add a document to a conversation.
    
    Args:
        conversation_id: Conversation ID
        document_id: Document ID
        service: Conversation service
        
    Returns:
        ConversationResponse: Updated conversation
        
    Raises:
        NotFoundException: If conversation or document not found
    """
    try:
        return await service.add_document(conversation_id, document_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(
    "/{conversation_id}/documents/{document_id}",
    response_model=ConversationResponse,
    summary="Remove Document from Conversation",
    description="Remove a document from a conversation"
)
async def remove_document(
    conversation_id: UUID,
    document_id: UUID,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Remove a document from a conversation.
    
    Args:
        conversation_id: Conversation ID
        document_id: Document ID
        service: Conversation service
        
    Returns:
        ConversationResponse: Updated conversation
        
    Raises:
        NotFoundException: If conversation or document not found
    """
    try:
        return await service.remove_document(conversation_id, document_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/{conversation_id}/query",
    response_model=str,
    summary="Query Conversation",
    description="Query a conversation using RAG"
)
async def query_conversation(
    conversation_id: UUID,
    query: str,
    service: ConversationService = Depends(get_conversation_service)
):
    """
    Query a conversation using RAG.
    
    Args:
        conversation_id: Conversation ID
        query: Query text
        service: Conversation service
        
    Returns:
        str: Response from the RAG chain
        
    Raises:
        NotFoundException: If conversation not found
        ValidationException: If no documents are found
    """
    try:
        return await service.query_conversation(conversation_id, query)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=404, detail=str(e)) 