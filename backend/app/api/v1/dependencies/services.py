from functools import lru_cache
from app.application.services.document_service import DocumentService
from app.application.services.conversation_service import ConversationService
from app.application.services.project_service import ProjectService
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.repositories.project_repository import ProjectRepository
from .vector_store import get_vector_store
from .rag_chain import get_rag_chain
from .document_processor import get_document_processor
from app.infrastructure.database.session import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@lru_cache()
def get_document_repository(db: Session = Depends(get_db)) -> DocumentRepository:
    """Get or create a DocumentRepository instance."""
    return DocumentRepository(db)

@lru_cache()
def get_conversation_repository(db: Session = Depends(get_db)) -> ConversationRepository:
    """Get or create a ConversationRepository instance."""
    return ConversationRepository(db)

@lru_cache()
def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Get or create a ProjectRepository instance."""
    return ProjectRepository(db)

@lru_cache()
def get_document_service(
    repository: DocumentRepository = Depends(get_document_repository),
    vector_store = Depends(get_vector_store)
) -> DocumentService:
    """Get or create a DocumentService instance."""
    # Initialize document sources
    document_sources = {
        "file": get_document_processor()
    }
    
    return DocumentService(
        repository=repository,
        vector_store=vector_store,
        document_sources=document_sources
    )

@lru_cache()
def get_conversation_service(
    repository: ConversationRepository = Depends(get_conversation_repository),
    vector_store = Depends(get_vector_store),
    rag_chain = Depends(get_rag_chain)
) -> ConversationService:
    """Get or create a ConversationService instance."""
    return ConversationService(
        repository=repository,
        vector_store=vector_store,
        rag_chain=rag_chain
    )

@lru_cache()
def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository),
    vector_store = Depends(get_vector_store)
) -> ProjectService:
    """Get or create a ProjectService instance."""
    return ProjectService(
        repository=repository,
        vector_store=vector_store
    ) 