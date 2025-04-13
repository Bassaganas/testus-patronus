from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Project
from app.db.session import get_db
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
            for key, value in project.dict(exclude={'id'}).items():
                setattr(existing, key, value)
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