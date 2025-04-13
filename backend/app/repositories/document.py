from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Document
from app.db.session import get_db
from datetime import datetime

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Document]:
        return self.db.query(Document).all()
    
    def get_by_id(self, id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == id).first()
    
    def get_by_conversation(self, conversation_id: str) -> List[Document]:
        return self.db.query(Document).filter(Document.conversation_id == conversation_id).all()
    
    def get_by_project(self, project_id: str) -> List[Document]:
        return self.db.query(Document).filter(Document.project_id == project_id).all()
    
    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def update(self, id: str, document: Document) -> Optional[Document]:
        existing = self.get_by_id(id)
        if existing:
            for key, value in document.dict(exclude={'id'}).items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return None
    
    def delete(self, id: str) -> bool:
        document = self.get_by_id(id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def delete_by_conversation(self, conversation_id: str) -> None:
        self.db.query(Document).filter(Document.conversation_id == conversation_id).delete()
        self.db.commit()
    
    def delete_by_project(self, project_id: str) -> None:
        self.db.query(Document).filter(Document.project_id == project_id).delete()
        self.db.commit() 