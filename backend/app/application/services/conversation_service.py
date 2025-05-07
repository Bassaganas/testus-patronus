from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, QueryResponse
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.rag.rag_chain import RAGChain
from app.core.exceptions import NotFoundException, ValidationException

class ConversationService:
    def __init__(self, repository: ConversationRepository, document_repository: DocumentRepository, vector_store: VectorStoreManager, rag_chain: RAGChain):
        self.repository = repository
        self.document_repository = document_repository
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
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The conversation ID
            role: The message role (must be 'user' or 'assistant')
            content: The message content
            
        Returns:
            ConversationResponse: Updated conversation
            
        Raises:
            NotFoundException: If conversation not found
            ValidationException: If message data is invalid
        """
        # Validate role
        if not role or role not in ["user", "assistant"]:
            raise ValidationException("Message role must be either 'user' or 'assistant'")
            
        # Validate content
        if not content:
            raise ValidationException("Message content cannot be empty")
            
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.add_message(conversation_id, {"role": role, "content": content})

    async def add_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.add_document(conversation_id, document_id)

    async def remove_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        conversation = await self.get_conversation_by_id(conversation_id)
        return await self.repository.remove_document(conversation_id, document_id)
        
    async def query_conversation(self, conversation_id: UUID, query: str, similarity_score: Optional[float] = None) -> str:
        """
        Query a conversation using RAG, fetching documents from both:
        1. The conversation's explicitly added documents
        2. All documents belonging to the conversation's project
        
        Args:
            conversation_id: The ID of the conversation
            query: The query text
            similarity_score: Optional minimum similarity score threshold for document retrieval (0.0 to 1.0)
            
        Returns:
            str: Response from the RAG chain
            
        Raises:
            NotFoundException: If conversation not found
            ValidationException: If no documents are found
        """
        conversation = await self.get_conversation_by_id(conversation_id)
        
        # Add the user query to the conversation before processing
        await self.add_message(conversation_id, "user", query)
        
        # Get project_id from the conversation
        project_id = conversation.project_id
        
        try:
            # Query the RAG chain with all available documents and similarity score
            response = await self.rag_chain.process_query(query, project_id, similarity_score=similarity_score)
            
            # Add the assistant's response to the conversation
            await self.add_message(conversation_id, "assistant", response)
            
            return response
        except Exception as e:
            error_msg = f"Error during RAG processing: {str(e)}"
            print(error_msg)
            # Still add a response to the conversation so the user knows something went wrong
            await self.add_message(conversation_id, "assistant", f"I'm sorry, I encountered an error: {str(e)}")
            raise ValidationException(error_msg) 