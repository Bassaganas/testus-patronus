from typing import List, Optional
from fastapi import HTTPException
from app.models import Project, ProjectCreate, ProjectUpdate
from app.repositories.project import ProjectRepository
from app.api.v1.exceptions import NotFoundError
from app.vector_store import VectorStoreManager
import logging
from app.services.database import db
from datetime import datetime

logger = logging.getLogger("testus-patronus")

class ProjectService:
    def __init__(self, vector_store: VectorStoreManager, project_repository: ProjectRepository):
        self.vector_store = vector_store
        self.project_repository = project_repository
        
    def create(self, project_create: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(
            title=project_create.title,
            description=project_create.description
        )
        return self.project_repository.create(project)
        
    def get(self, project_id: str) -> Project:
        """Get a project by ID."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project
        
    def get_all(self) -> List[Project]:
        """Get all projects."""
        return self.project_repository.get_all()
        
    def update(self, project_id: str, project_update: ProjectUpdate) -> Project:
        """Update a project."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
            
        # Create a new Project instance with only the updateable fields
        update_data = project_update.model_dump(exclude_unset=True)
        updated_project = Project(
            id=project_id,  # Preserve the original ID
            created_at=project.created_at,  # Preserve the original created_at
            updated_at=datetime.utcnow(),  # Set new updated_at
            documents=[doc.id for doc in project.documents],  # Convert document objects to IDs
            conversations=[conv.id for conv in project.conversations],  # Convert conversation objects to IDs
            **update_data
        )
        
        return self.project_repository.update(project_id, updated_project)
        
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        
        # Delete project documents from vector store
        if project.documents:
            for doc in project.documents:
                try:
                    self.vector_store.delete_document(doc.id)
                except Exception as e:
                    logger.warning(f"Failed to delete document {doc.id} from vector store: {e}")
        
        # Delete associated documents
        db.documents.delete_by_project(project_id)
        
        return self.project_repository.delete(project_id) 