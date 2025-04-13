from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models import Project, ProjectCreate, ProjectUpdate
from app.db.session import get_db
from app.db.models import Project as DBProject
from app.vector_store import VectorStoreManager
from app.api.v1.exceptions import NotFoundError, ValidationError
from app.api.v1.dependencies.vector_store import get_vector_store
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get(
    "",
    response_model=List[Project],
    summary="Get All Projects",
    description="Retrieve a list of all projects"
)
async def get_projects(db: Session = Depends(get_db)):
    """
    Get all projects.
    
    Args:
        db: Database session
        
    Returns:
        List[Project]: List of all projects
    """
    return db.query(DBProject).all()

@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get Project",
    description="Retrieve a specific project by ID"
)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """
    Get a specific project by ID.
    
    Args:
        project_id: The ID of the project to retrieve
        db: Database session
        
    Returns:
        Project: The requested project
        
    Raises:
        NotFoundError: If project is not found
    """
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise NotFoundError("Project", project_id)
    return project

@router.post(
    "",
    response_model=Project,
    summary="Create Project",
    description="Create a new project"
)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    
    Args:
        project: The project data to create
        db: Database session
        
    Returns:
        Project: The created project
    """
    db_project = DBProject(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put(
    "/{project_id}",
    response_model=Project,
    summary="Update Project",
    description="Update an existing project"
)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
    vector_store: VectorStoreManager = Depends(get_vector_store)
):
    """
    Update an existing project.
    
    Args:
        project_id: The ID of the project to update
        project: The updated project data (only title and description can be modified)
        db: Database session
        vector_store: Vector store manager (injected)
        
    Returns:
        Project: The updated project
        
    Raises:
        NotFoundError: If project is not found
        ValidationError: If project ID mismatch
    """
    # Get existing project
    existing_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not existing_project:
        raise NotFoundError("Project", project_id)
    
    # Update only allowed fields
    update_data = project.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(existing_project, key):
            setattr(existing_project, key, value)
    
    # Update timestamp
    existing_project.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(existing_project)
    return existing_project

@router.delete(
    "/{project_id}",
    summary="Delete Project",
    description="Delete a project and its associated documents"
)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    vector_store: VectorStoreManager = Depends(get_vector_store)
):
    """
    Delete a project and its associated documents.
    
    Args:
        project_id: The ID of the project to delete
        db: Database session
        vector_store: Vector store manager (injected)
        
    Returns:
        dict: Success message
        
    Raises:
        NotFoundError: If project is not found
    """
    # Delete project documents from vector store
    vector_store.delete_project_documents(project_id)
    
    # Get and delete the project
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise NotFoundError("Project", project_id)
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"} 