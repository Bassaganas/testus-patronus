from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectCreate, ProjectUpdate
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
    db_projects = db.query(DBProject).all()
    return [
        Project(
            id=project.id,
            title=project.title,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            documents=[doc.id for doc in project.documents],
            conversations=[conv.id for conv in project.conversations]
        ) for project in db_projects
    ]

@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get Project by ID",
    description="Retrieve a specific project by its ID"
)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """
    Get a project by ID.
    
    Args:
        project_id: Project ID
        db: Database session
        
    Returns:
        Project: Project details
        
    Raises:
        NotFoundError: If project not found
    """
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise NotFoundError(f"Project with ID {project_id} not found")
    return Project(
        id=project.id,
        title=project.title,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        documents=[doc.id for doc in project.documents],
        conversations=[conv.id for conv in project.conversations]
    )

@router.post(
    "",
    response_model=Project,
    summary="Create Project",
    description="Create a new project"
)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    vector_store: VectorStoreManager = Depends(get_vector_store)
):
    """
    Create a new project.
    
    Args:
        project: Project data
        db: Database session
        vector_store: Vector store manager
        
    Returns:
        Project: Created project
        
    Raises:
        ValidationError: If project data is invalid
    """
    try:
        db_project = DBProject(
            title=project.title,
            description=project.description
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return Project(
            id=db_project.id,
            title=db_project.title,
            description=db_project.description,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            documents=[doc.id for doc in db_project.documents],
            conversations=[conv.id for conv in db_project.conversations]
        )
    except Exception as e:
        db.rollback()
        raise ValidationError(f"Failed to create project: {str(e)}")

@router.put(
    "/{project_id}",
    response_model=Project,
    summary="Update Project",
    description="Update an existing project"
)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a project.
    
    Args:
        project_id: Project ID
        project: Updated project data
        db: Database session
        
    Returns:
        Project: Updated project
        
    Raises:
        NotFoundError: If project not found
        ValidationError: If project data is invalid
    """
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        raise NotFoundError(f"Project with ID {project_id} not found")
    
    try:
        for key, value in project.model_dump(exclude_unset=True).items():
            setattr(db_project, key, value)
        db_project.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_project)
        return Project(
            id=db_project.id,
            title=db_project.title,
            description=db_project.description,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            documents=[doc.id for doc in db_project.documents],
            conversations=[conv.id for conv in db_project.conversations]
        )
    except Exception as e:
        db.rollback()
        raise ValidationError(f"Failed to update project: {str(e)}")

@router.delete(
    "/{project_id}",
    response_model=Project,
    summary="Delete Project",
    description="Delete a project and its associated data"
)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    vector_store: VectorStoreManager = Depends(get_vector_store)
):
    """
    Delete a project.
    
    Args:
        project_id: Project ID
        db: Database session
        vector_store: Vector store manager
        
    Returns:
        Project: Deleted project
        
    Raises:
        NotFoundError: If project not found
        ValidationError: If deletion fails
    """
    db_project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not db_project:
        raise NotFoundError(f"Project with ID {project_id} not found")
    
    try:
        # Delete associated vector store data
        vector_store.delete_project_documents(project_id)
        
        # Delete from database
        db.delete(db_project)
        db.commit()
        return Project(
            id=db_project.id,
            title=db_project.title,
            description=db_project.description,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            documents=[doc.id for doc in db_project.documents],
            conversations=[conv.id for conv in db_project.conversations]
        )
    except Exception as e:
        db.rollback()
        raise ValidationError(f"Failed to delete project: {str(e)}") 