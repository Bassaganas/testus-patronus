from fastapi import Depends
from app.infrastructure.database.session import get_db
from app.application.service_factory import ServiceFactory

def get_service_factory(db=Depends(get_db)):
    return ServiceFactory(db)

def get_document_service(factory=Depends(get_service_factory)):
    return factory.document_service()

def get_conversation_service(factory=Depends(get_service_factory)):
    return factory.conversation_service()

def get_project_service(factory=Depends(get_service_factory)):
    return factory.project_service() 