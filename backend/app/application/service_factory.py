from app.infrastructure.repositories.document_repository import DocumentRepository
from app.infrastructure.repositories.conversation_repository import ConversationRepository
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.application.services.document_service import DocumentService
from app.application.services.conversation_service import ConversationService
from app.application.services.project_service import ProjectService
from app.infrastructure.factories.vector_store_factory import VectorStoreFactory
from app.infrastructure.factories.rag_chain_factory import RAGChainFactory
from app.infrastructure.factories.document_processor_factory import DocumentProcessorFactory

class ServiceFactory:
    def __init__(self, db):
        self.db = db

    def document_service(self):
        repository = DocumentRepository(self.db)
        vector_store = VectorStoreFactory.get_vector_store()
        document_sources = {"file": DocumentProcessorFactory.get_document_processor()}
        return DocumentService(repository, vector_store, document_sources)

    def conversation_service(self):
        repository = ConversationRepository(self.db)
        document_repository = DocumentRepository(self.db)
        vector_store = VectorStoreFactory.get_vector_store()
        rag_chain = RAGChainFactory.get_rag_chain()
        return ConversationService(repository, document_repository, vector_store, rag_chain)

    def project_service(self):
        repository = ProjectRepository(self.db)
        vector_store = VectorStoreFactory.get_vector_store()
        return ProjectService(repository, vector_store) 