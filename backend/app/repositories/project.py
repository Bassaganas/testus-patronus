from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Project, Document
from datetime import datetime

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Project]:
        return self.db.query(Project).all()
    
    def get_by_id(self, id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == id).first()
    
    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def update(self, id: str, project: Project) -> Optional[Project]:
        existing = self.get_by_id(id)
        if existing:
            # Exclude id, created_at, and updated_at from updates
            excluded_fields = {'id', 'created_at', 'updated_at', 'documents', 'conversations'}
            update_data = project.dict(exclude=excluded_fields)
            
            # Only update allowed fields
            for key, value in update_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            
            # Update the updated_at timestamp
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return None
    
    def delete(self, id: str) -> bool:
        project = self.get_by_id(id)
        if project:
            self.db.delete(project)
            self.db.commit()
            return True
        return False
    
    def add_document(self, project_id: str, document_id: str) -> Optional[Project]:
        """Add a document to a project."""
        project = self.get_by_id(project_id)
        if project:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if document:
                project.documents.append(document)
                self.db.commit()
                self.db.refresh(project)
                return project
        return None
    
    def remove_document(self, project_id: str, document_id: str) -> Optional[Project]:
        """Remove a document from a project."""
        project = self.get_by_id(project_id)
        if project:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if document in project.documents:
                project.documents.remove(document)
                self.db.commit()
                self.db.refresh(project)
                return project
        return None 