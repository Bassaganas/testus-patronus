from typing import List, Optional
from fastapi import HTTPException
from app.models.conversation import Conversation, Message
from app.models.chat import ChatRequest, ChatResponse
from app.services.database import db
from app.vector_store import VectorStoreManager
from app.rag_chain import RAGChain
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger("testus-patronus")

class ConversationService:
    def __init__(self, vector_store: VectorStoreManager, rag_chain: RAGChain):
        self.vector_store = vector_store
        self.rag_chain = rag_chain
        
    async def get_conversations(self, project_id: Optional[str] = None) -> List[Conversation]:
        """Get all conversations, optionally filtered by project."""
        if project_id:
            return db.conversations.get_by_project(project_id)
        return db.conversations.get_all()
        
    async def get_conversation(self, conversation_id: str) -> Conversation:
        """Get a specific conversation."""
        conversation = db.conversations.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        return conversation
        
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        return db.conversations.create(conversation)
        
    async def update_conversation(self, conversation_id: str, conversation: Conversation) -> Conversation:
        """Update a conversation."""
        if conversation_id != conversation.id:
            raise HTTPException(status_code=400, detail="Conversation ID mismatch")
            
        updated_conv = db.conversations.update(conversation_id, conversation)
        if not updated_conv:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
            
        return updated_conv
        
    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and its associated documents."""
        conversation = await self.get_conversation(conversation_id)
        
        # Delete conversation documents from vector store
        self.vector_store.delete_conversation_documents(conversation_id)
        
        # Delete associated documents
        db.documents.delete_by_conversation(conversation_id)
        
        # Delete the conversation
        if not db.conversations.delete(conversation_id):
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
            
    async def query_conversation(
        self,
        conversation_id: str,
        request: ChatRequest
    ) -> ChatResponse:
        """Process a query in the context of a conversation."""
        try:
            # Verify conversation exists
            conversation = await self.get_conversation(conversation_id)
            
            # Create user message
            user_message = Message(
                id=str(uuid4()),
                role="user",
                content=request.query,
                timestamp=datetime.now()
            )
            
            # Add user message to conversation
            updated_conv = db.conversations.add_message(conversation_id, user_message)
            if not updated_conv:
                raise HTTPException(status_code=500, detail="Failed to save user message")
            
            # Get response from RAG chain
            response_content = self.rag_chain.get_response(
                query=request.query,
                conversation_id=conversation_id,
                project_id=request.project_id
            )
            
            # Create assistant message
            assistant_message = Message(
                id=str(uuid4()),
                role="assistant",
                content=response_content,
                timestamp=datetime.now()
            )
            
            # Add assistant message to conversation
            updated_conv = db.conversations.add_message(conversation_id, assistant_message)
            if not updated_conv:
                raise HTTPException(status_code=500, detail="Failed to save assistant message")
            
            return ChatResponse(
                response=response_content,
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_message=assistant_message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in query_conversation: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 