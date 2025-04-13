from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.models import Project
from app.db.session import get_db
from app.repositories.project import ProjectRepository
from app.vector_store import VectorStoreManager
from datetime import datetime
import logging

logger = logging.getLogger("testus-patronus")

class ProjectService:
    def __init__(self, vector_store: VectorStoreManager, db: Session = Depends(get_db)):
        self.db = db
        self.repository = ProjectRepository(db)
        self.vector_store = vector_store
        
    async def get_projects(self) -> List[Project]:
        """Get all projects."""
        return self.repository.get_all()
        
    async def get_project(self, project_id: str) -> Project:
        """Get a specific project."""
        project = self.repository.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return project
        
    async def create_project(self, project: Project) -> Project:
        """Create a new project."""
        try:
            # Set default timestamps
            if not project.created_at:
                project.created_at = datetime.utcnow()
            project.updated_at = datetime.utcnow()
            
            # Create project in database
            created_project = self.repository.create(project)
            return created_project
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
            
    async def update_project(self, project_id: str, project: Project) -> Project:
        """Update a project."""
        db_project = await self.get_project(project_id)
        
        # Update fields
        for key, value in project.dict(exclude={'id'}).items():
            setattr(db_project, key, value)
        
        db_project.updated_at = datetime.utcnow()
        
        # Update project in database
        updated_project = self.repository.update(project_id, db_project)
        if not updated_project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        return updated_project
        
    async def delete_project(self, project_id: str) -> None:
        """Delete a project and its related resources."""
        # First check if project exists
        project = await self.get_project(project_id)
        
        # Delete from database
        result = self.repository.delete(project_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Delete related documents from vector store if needed
        # This may need to be implemented based on your application's needs 