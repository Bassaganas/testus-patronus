from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domain.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.infrastructure.database.models.project import Project
from app.core.exceptions import NotFoundException

class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[ProjectResponse]:
        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.documents),
                selectinload(Project.conversations)
            )
        )
        projects = result.scalars().all()
        
        # Convert to response models with document and conversation IDs
        response_models = []
        for project in projects:
            # Create a dict representation of the project
            proj_dict = {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "documents": [str(doc.id) for doc in project.documents],
                "conversations": [str(conv.id) for conv in project.conversations]
            }
            response_models.append(ProjectResponse.model_validate(proj_dict))
            
        return response_models

    async def get_by_id(self, project_id: UUID) -> ProjectResponse:
        result = await self.db.execute(
            select(Project)
            .where(Project.id == str(project_id))
            .options(
                selectinload(Project.documents),
                selectinload(Project.conversations)
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
            
        # Create a dict representation of the project
        proj_dict = {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "documents": [str(doc.id) for doc in project.documents],
            "conversations": [str(conv.id) for conv in project.conversations]
        }
        return ProjectResponse.model_validate(proj_dict)

    async def create(self, project: ProjectCreate) -> ProjectResponse:
        # Convert project data to dict and ensure id is a string if provided
        project_data = project.model_dump()
        if project_data.get("id"):
            project_data["id"] = str(project_data["id"])
        
        db_project = Project(**project_data)
        self.db.add(db_project)
        await self.db.commit()
        await self.db.refresh(db_project)
        
        # Reload the project with relationships
        result = await self.db.execute(
            select(Project)
            .where(Project.id == db_project.id)
            .options(
                selectinload(Project.documents),
                selectinload(Project.conversations)
            )
        )
        db_project = result.scalar_one()
        
        # Create a dict representation of the project
        proj_dict = {
            "id": db_project.id,
            "title": db_project.title,
            "description": db_project.description,
            "created_at": db_project.created_at,
            "updated_at": db_project.updated_at,
            "documents": [str(doc.id) for doc in db_project.documents],
            "conversations": [str(conv.id) for conv in db_project.conversations]
        }
        return ProjectResponse.model_validate(proj_dict)

    async def update(self, project_id: UUID, project: ProjectUpdate) -> ProjectResponse:
        result = await self.db.execute(
            select(Project)
            .where(Project.id == str(project_id))
            .options(
                selectinload(Project.documents),
                selectinload(Project.conversations)
            )
        )
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise NotFoundException(f"Project with id {project_id} not found")
            
        update_data = project.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        await self.db.commit()
        await self.db.refresh(db_project)
        
        # Create a dict representation of the project
        proj_dict = {
            "id": db_project.id,
            "title": db_project.title,
            "description": db_project.description,
            "created_at": db_project.created_at,
            "updated_at": db_project.updated_at,
            "documents": [str(doc.id) for doc in db_project.documents],
            "conversations": [str(conv.id) for conv in db_project.conversations]
        }
        return ProjectResponse.model_validate(proj_dict)

    async def delete(self, project_id: UUID) -> None:
        result = await self.db.execute(
            select(Project)
            .where(Project.id == str(project_id))
            .options(
                selectinload(Project.documents),
                selectinload(Project.conversations)
            )
        )
        db_project = result.scalar_one_or_none()
        if not db_project:
            raise NotFoundException(f"Project with id {project_id} not found")
            
        await self.db.delete(db_project)
        await self.db.commit() 