from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.document import Document
from app.core.exceptions import NotFoundException

class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, project_id: Optional[str] = None) -> List[ConversationResponse]:
        query = select(Conversation).options(
            selectinload(Conversation.documents)
        )
        
        if project_id:
            query = query.where(Conversation.project_id == str(project_id))
            
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        # Convert to response models with document IDs
        response_models = []
        for conversation in conversations:
            # Create a dict representation of the conversation
            conv_dict = {
                "id": conversation.id,
                "title": conversation.title,
                "project_id": conversation.project_id,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "messages": conversation.messages or [],
                "documents": [str(doc.id) for doc in conversation.documents]
            }
            response_models.append(ConversationResponse.model_validate(conv_dict))
            
        return response_models

    async def get_by_id(self, conversation_id: UUID) -> ConversationResponse:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == str(conversation_id))
            .options(selectinload(Conversation.documents))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise NotFoundException(f"Conversation with id {conversation_id} not found")
            
        # Create a dict representation of the conversation
        conv_dict = {
            "id": conversation.id,
            "title": conversation.title,
            "project_id": conversation.project_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": conversation.messages or [],
            "documents": [str(doc.id) for doc in conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict)

    async def create(self, conversation: ConversationCreate) -> ConversationResponse:
        db_conversation = Conversation(**conversation.model_dump())
        self.db.add(db_conversation)
        await self.db.commit()
        await self.db.refresh(db_conversation)
        
        # Reload the conversation with relationships
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == db_conversation.id)
            .options(selectinload(Conversation.documents))
        )
        db_conversation = result.scalar_one()
        
        # Create a dict representation of the conversation
        conv_dict = {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "project_id": db_conversation.project_id,
            "created_at": db_conversation.created_at,
            "updated_at": db_conversation.updated_at,
            "messages": db_conversation.messages or [],
            "documents": [str(doc.id) for doc in db_conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict)

    async def update(self, conversation_id: UUID, conversation: ConversationUpdate) -> ConversationResponse:
        db_conversation = await self.get_by_id(conversation_id)
        update_data = conversation.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_conversation, key, value)
        await self.db.commit()
        await self.db.refresh(db_conversation)
        
        # Reload the conversation with relationships
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == str(conversation_id))
            .options(selectinload(Conversation.documents))
        )
        db_conversation = result.scalar_one()
        
        # Create a dict representation of the conversation
        conv_dict = {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "project_id": db_conversation.project_id,
            "created_at": db_conversation.created_at,
            "updated_at": db_conversation.updated_at,
            "messages": db_conversation.messages or [],
            "documents": [str(doc.id) for doc in db_conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict)

    async def delete(self, conversation_id: UUID) -> None:
        db_conversation = await self.get_by_id(conversation_id)
        await self.db.delete(db_conversation)
        await self.db.commit()

    async def add_message(self, conversation_id: UUID, message: dict) -> ConversationResponse:
        db_conversation = await self.get_by_id(conversation_id)
        if not db_conversation.messages:
            db_conversation.messages = []
        db_conversation.messages.append(message)
        await self.db.commit()
        await self.db.refresh(db_conversation)
        
        # Reload the conversation with relationships
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == str(conversation_id))
            .options(selectinload(Conversation.documents))
        )
        db_conversation = result.scalar_one()
        
        # Create a dict representation of the conversation
        conv_dict = {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "project_id": db_conversation.project_id,
            "created_at": db_conversation.created_at,
            "updated_at": db_conversation.updated_at,
            "messages": db_conversation.messages or [],
            "documents": [str(doc.id) for doc in db_conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict)

    async def add_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        db_conversation = await self.get_by_id(conversation_id)
        result = await self.db.execute(
            select(Document).where(Document.id == str(document_id))
        )
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundException(f"Document with id {document_id} not found")
        
        if document not in db_conversation.documents:
            db_conversation.documents.append(document)
            await self.db.commit()
            await self.db.refresh(db_conversation)
        
        # Reload the conversation with relationships
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == str(conversation_id))
            .options(selectinload(Conversation.documents))
        )
        db_conversation = result.scalar_one()
        
        # Create a dict representation of the conversation
        conv_dict = {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "project_id": db_conversation.project_id,
            "created_at": db_conversation.created_at,
            "updated_at": db_conversation.updated_at,
            "messages": db_conversation.messages or [],
            "documents": [str(doc.id) for doc in db_conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict)

    async def remove_document(self, conversation_id: UUID, document_id: UUID) -> ConversationResponse:
        db_conversation = await self.get_by_id(conversation_id)
        result = await self.db.execute(
            select(Document).where(Document.id == str(document_id))
        )
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundException(f"Document with id {document_id} not found")
        
        if document in db_conversation.documents:
            db_conversation.documents.remove(document)
            await self.db.commit()
            await self.db.refresh(db_conversation)
        
        # Reload the conversation with relationships
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == str(conversation_id))
            .options(selectinload(Conversation.documents))
        )
        db_conversation = result.scalar_one()
        
        # Create a dict representation of the conversation
        conv_dict = {
            "id": db_conversation.id,
            "title": db_conversation.title,
            "project_id": db_conversation.project_id,
            "created_at": db_conversation.created_at,
            "updated_at": db_conversation.updated_at,
            "messages": db_conversation.messages or [],
            "documents": [str(doc.id) for doc in db_conversation.documents]
        }
        return ConversationResponse.model_validate(conv_dict) 