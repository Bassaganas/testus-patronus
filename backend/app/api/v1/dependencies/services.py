from functools import lru_cache
from app.services.document_service import DocumentService
from app.services.conversation_service import ConversationService
from app.services.project_service import ProjectService
from .vector_store import get_vector_store
from .rag_chain import get_rag_chain
from .document_processor import get_document_processor
from app.db.session import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@lru_cache()
def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Get or create a DocumentService instance."""
    return DocumentService(
        db=db,
        vector_store=get_vector_store(),
        doc_processor=get_document_processor()
    )

@lru_cache()
def get_conversation_service() -> ConversationService:
    """Get or create a ConversationService instance."""
    return ConversationService(
        vector_store=get_vector_store(),
        rag_chain=get_rag_chain()
    )

@lru_cache()
def get_project_service() -> ProjectService:
    """Get or create a ProjectService instance."""
    return ProjectService(
        vector_store=get_vector_store()
    ) 