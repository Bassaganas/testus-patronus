from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.application.services.project_service import ProjectService
from app.infrastructure.database.session import get_db
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/projects", tags=["Projects"])

async def get_project_service(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStoreManager = Depends(VectorStoreManager)
) -> ProjectService:
    """
    Get project service
    """
    repository = ProjectRepository(db)
    return ProjectService(repository, vector_store)

@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="Get All Projects",
    description="Retrieve a list of all projects"
)
async def get_projects(
    service: ProjectService = Depends(get_project_service)
):
    """
    Get all projects.
    
    Args:
        service: Project service
        
    Returns:
        List[ProjectResponse]: List of all projects
    """
    return await service.get_all_projects()

@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get Project by ID",
    description="Retrieve a specific project by its ID"
)
async def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service)
):
    """
    Get a project by ID.
    
    Args:
        project_id: Project ID
        service: Project service
        
    Returns:
        ProjectResponse: Project details
        
    Raises:
        NotFoundException: If project not found
    """
    try:
        return await service.get_project_by_id(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "",
    response_model=ProjectResponse,
    summary="Create Project",
    description="Create a new project"
)
async def create_project(
    project: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    """
    Create a new project.
    
    Args:
        project: Project data
        service: Project service
        
    Returns:
        ProjectResponse: Created project
        
    Raises:
        ValidationException: If project data is invalid
    """
    try:
        return await service.create_project(project)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update Project",
    description="Update an existing project"
)
async def update_project(
    project_id: UUID,
    project: ProjectUpdate,
    service: ProjectService = Depends(get_project_service)
):
    """
    Update a project.
    
    Args:
        project_id: Project ID
        project: Project data
        service: Project service
        
    Returns:
        ProjectResponse: Updated project
        
    Raises:
        NotFoundException: If project not found
        ValidationException: If project data is invalid
    """
    try:
        return await service.update_project(project_id, project)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Delete Project",
    description="Delete a project and its associated data"
)
async def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service)
):
    """
    Delete a project.
    
    Args:
        project_id: Project ID
        service: Project service
        
    Returns:
        ProjectResponse: Deleted project
        
    Raises:
        NotFoundException: If project not found
    """
    try:
        # Get the project data before deletion
        project = await service.get_project_by_id(project_id)
        # Delete the project
        await service.delete_project(project_id)
        return project
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e)) 