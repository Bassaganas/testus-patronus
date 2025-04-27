from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.application.services.project_service import ProjectService
from app.api.container import get_project_service
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/projects", tags=["Projects"])

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
        # Ensure project ID is a string if provided
        if project.id:
            project.id = str(project.id)
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
        # Delete the project and return the project data
        return await service.delete_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e)) 