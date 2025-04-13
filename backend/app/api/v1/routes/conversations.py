from fastapi import APIRouter, Depends, Query, HTTPException, Form
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.db.models import Conversation, Document
from app.api.v1.exceptions import NotFoundError, ValidationError
from app.api.v1.dependencies.vector_store import get_vector_store
from app.api.v1.dependencies.rag_chain import get_rag_chain
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse
from app.schemas.document import DocumentResponse

logger = logging.getLogger("testus-patronus")
router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get(
    "",
    response_model=List[ConversationResponse],
    summary="Get All Conversations",
    description="Retrieve a list of all conversations, optionally filtered by project"
)
async def get_conversations(
    project_id: Optional[str] = Query(None, description="Filter conversations by project ID"),
    db: Session = Depends(get_db)
) -> List[ConversationResponse]:
    """
    Get all conversations, optionally filtered by project.
    
    Args:
        project_id: Optional project ID to filter conversations
        db: Database session
        
    Returns:
        List[ConversationResponse]: List of conversations
    """
    query = db.query(Conversation)
    if project_id:
        query = query.filter(Conversation.project_id == project_id)
    return query.all()

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get Conversation",
    description="Retrieve a specific conversation by ID"
)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        db: Database session
        
    Returns:
        ConversationResponse: The requested conversation
        
    Raises:
        NotFoundError: If conversation is not found
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise NotFoundError("Conversation", conversation_id)
    return conversation

@router.post(
    "",
    response_model=ConversationResponse,
    summary="Create Conversation",
    description="Create a new conversation"
)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Create a new conversation.
    
    Args:
        conversation: The conversation to create
        db: Database session
        
    Returns:
        ConversationResponse: The created conversation
    """
    db_conversation = Conversation(**conversation.model_dump())
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update Conversation",
    description="Update an existing conversation"
)
async def update_conversation(
    conversation_id: str,
    conversation: ConversationUpdate,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Update an existing conversation.
    
    Args:
        conversation_id: The ID of the conversation to update
        conversation: The updated conversation data
        db: Database session
        
    Returns:
        ConversationResponse: The updated conversation
        
    Raises:
        NotFoundError: If conversation is not found
    """
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conversation:
        raise NotFoundError("Conversation", conversation_id)
    
    for key, value in conversation.model_dump(exclude_unset=True).items():
        setattr(db_conversation, key, value)
    
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.delete(
    "/{conversation_id}",
    summary="Delete Conversation",
    description="Delete a conversation and its associated documents"
)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    vector_store = Depends(get_vector_store)
):
    """
    Delete a conversation and its associated documents.
    
    Args:
        conversation_id: The ID of the conversation to delete
        db: Database session
        vector_store: Vector store manager
        
    Returns:
        dict: Success message
        
    Raises:
        NotFoundError: If conversation is not found
    """
    db_conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conversation:
        raise NotFoundError("Conversation", conversation_id)
    
    # Delete conversation documents from vector store
    vector_store.delete_conversation_documents(conversation_id)
    
    # Delete conversation and its related documents from database
    db.delete(db_conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}

@router.post(
    "/{conversation_id}/query",
    summary="Query Conversation",
    description="Send a query in the context of a conversation"
)
async def query_conversation(
    conversation_id: str,
    query: str = Form(...),
    db: Session = Depends(get_db),
    vector_store = Depends(get_vector_store),
    rag_chain = Depends(get_rag_chain)
):
    """
    Send a query in the context of a conversation.
    This endpoint uses RAG to find relevant documents and generate a response.
    
    Args:
        conversation_id: The ID of the conversation
        query: The query text
        db: Database session
        vector_store: Vector store manager
        rag_chain: RAG chain service
        
    Returns:
        dict: Response from the RAG chain
        
    Raises:
        NotFoundError: If conversation is not found
        ValidationError: If no documents are found
    """
    # Get the conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise NotFoundError("Conversation", conversation_id)
    
    # Get documents for this conversation
    documents = db.query(Document).filter(Document.conversation_id == conversation_id).all()
    if not documents:
        raise ValidationError("No documents found in this conversation. Please upload documents first.")
    
    # Process the query using RAG
    response = await rag_chain.process_query(query, documents)
    
    # Update conversation with the new message
    if not conversation.messages:
        conversation.messages = []
    
    conversation.messages.append({
        "role": "user",
        "content": query
    })
    conversation.messages.append({
        "role": "assistant",
        "content": response
    })
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "response": response,
        "conversation_id": conversation_id
    } 