from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.core.exceptions import NotFoundException, ValidationException

class ProjectService:
    def __init__(self, repository: ProjectRepository, vector_store: VectorStoreManager):
        self.repository = repository
        self.vector_store = vector_store

    async def get_all_projects(self) -> List[ProjectResponse]:
        return await self.repository.get_all()

    async def get_project_by_id(self, project_id: UUID) -> ProjectResponse:
        project = await self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        return project

    async def create_project(self, project: ProjectCreate) -> ProjectResponse:
        return await self.repository.create(project)

    async def update_project(self, project_id: UUID, project: ProjectUpdate) -> ProjectResponse:
        existing_project = await self.get_project_by_id(project_id)
        return await self.repository.update(project_id, project)

    async def delete_project(self, project_id: UUID) -> ProjectResponse:
        project = await self.get_project_by_id(project_id)
        await self.repository.delete(project_id)
        return project 