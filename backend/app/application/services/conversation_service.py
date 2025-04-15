from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, QueryResponse
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.rag.rag_chain import RAGChain
from app.core.exceptions import NotFoundException, ValidationException

class ConversationService:
    def __init__(self, repository: ConversationRepository, vector_store: VectorStoreManager, rag_chain: RAGChain):
        self.repository = repository
        self.vector_store = vector_store
        self.rag_chain = rag_chain

    async def get_all_conversations(self, project_id: Optional[str] = None) -> List[ConversationResponse]:
        return await self.repository.get_all(project_id)

    async def get_conversation_by_id(self, conversation_id: UUID) -> ConversationResponse:
        conversation = await self.repository.get_by_id(conversation_id)
        if not conversation:
            raise NotFoundException(f"Conversation with id {conversation_id} not found")
        return conversation

    async def create_conversation(self, conversation: ConversationCreate) -> ConversationResponse:
        return await self.repository.create(conversation)

    async def update_conversation(self, conversation_id: UUID, conversation: ConversationUpdate) -> ConversationResponse:
        existing_conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.update(conversation_id, conversation)

    async def delete_conversation(self, conversation_id: UUID) -> None:
        conversation = await self.get_conversation_by_id(conversation_id)
        await self.repository.delete(conversation_id)
        # Delete associated documents from vector store
        self.vector_store.delete_conversation_documents(conversation_id)

    async def add_message(self, conversation_id: UUID, role: str, content: str) -> ConversationResponse:
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.add_message(conversation_id, {"role": role, "content": content})

    async def add_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.add_document(conversation_id, document_id)

    async def remove_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.remove_document(conversation_id, document_id)
        
    async def query_conversation(self, conversation_id: UUID, query: str) -> str:
        """
        Query a conversation using RAG.
        
        Args:
            conversation_id: The ID of the conversation
            query: The query text
            
        Returns:
            str: Response from the RAG chain
            
        Raises:
            NotFoundException: If conversation not found
            ValidationException: If no documents are found
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        
        # Check if conversation has documents
        if not conversation.documents:
            raise ValidationException("No documents found in conversation")
            
        # Get document IDs
        document_ids = conversation.documents
        
        # Query the RAG chain
        response = await self.rag_chain.process_query(query, document_ids)
        
        # Add the query and response to the conversation
        await self.add_message(conversation_id, "user", query)
        await self.add_message(conversation_id, "assistant", response)
        
        return response 