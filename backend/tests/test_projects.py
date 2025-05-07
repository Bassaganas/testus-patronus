import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from app.domain.models.project import Project
from app.domain.schemas.project import ProjectCreate, ProjectUpdate
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.application.services.project_service import ProjectService

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def project_repository(mock_db):
    return ProjectRepository(mock_db)

@pytest.fixture
def project_service(project_repository):
    return ProjectService(project_repository)

@pytest.fixture
def sample_project_data():
    return {
        "id": "test-id-123",
        "title": "Test Project",
        "description": "This is a test project",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "documents": []
    }

@pytest.fixture
def sample_project(sample_project_data):
    return Project(**sample_project_data)

class TestProjectRepository:
    def test_create_project(self, project_repository, mock_db, sample_project):
        # Arrange
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = project_repository.create(sample_project)
        
        # Assert
        assert result == sample_project
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_project_by_id_exists(self, project_repository, mock_db, sample_project):
        # Arrange
        mock_db.query().filter().first.return_value = sample_project
        
        # Act
        result = project_repository.get_by_id(sample_project.id)
        
        # Assert
        assert result == sample_project

    def test_get_project_by_id_not_exists(self, project_repository, mock_db):
        # Arrange
        mock_db.query().filter().first.return_value = None
        
        # Act
        result = project_repository.get_by_id("non-existent-id")
        
        # Assert
        assert result is None

    def test_update_project(self, project_repository, mock_db, sample_project):
        # Arrange
        mock_db.query().filter().first.return_value = sample_project
        update_data = ProjectUpdate(
            title="Updated Title",
            description="Updated description"
        )
        
        # Act
        result = project_repository.update(sample_project.id, update_data)
        
        # Assert
        assert result.title == "Updated Title"
        assert result.description == "Updated description"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_delete_project(self, project_repository, mock_db, sample_project):
        # Arrange
        mock_db.query().filter().first.return_value = sample_project
        
        # Act
        result = project_repository.delete(sample_project.id)
        
        # Assert
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

class TestProjectService:
    def test_create_project(self, project_service, project_repository, sample_project_data):
        # Arrange
        project_create = ProjectCreate(
            title=sample_project_data["title"],
            description=sample_project_data["description"]
        )
        project_repository.create = Mock(return_value=Project(**sample_project_data))
        
        # Act
        result = project_service.create(project_create)
        
        # Assert
        assert result.title == sample_project_data["title"]
        assert result.description == sample_project_data["description"]
        project_repository.create.assert_called_once()

    def test_get_project_not_found(self, project_service, project_repository):
        # Arrange
        project_repository.get_by_id = Mock(return_value=None)
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            project_service.get("non-existent-id")

    def test_update_project(self, project_service, project_repository, sample_project):
        # Arrange
        project_repository.get_by_id = Mock(return_value=sample_project)
        project_repository.update = Mock(return_value=sample_project)
        update_data = ProjectUpdate(
            title="Updated Title",
            description="Updated description"
        )
        
        # Act
        result = project_service.update(sample_project.id, update_data)
        
        # Assert
        assert result.title == "Updated Title"
        assert result.description == "Updated description"
        project_repository.update.assert_called_once()

    def test_delete_project(self, project_service, project_repository, sample_project):
        # Arrange
        project_repository.get_by_id = Mock(return_value=sample_project)
        project_repository.delete = Mock(return_value=True)
        
        # Act
        result = project_service.delete(sample_project.id)
        
        # Assert
        assert result is True
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Project
from app.database import Database
from datetime import datetime

def test_project_creation():
    # Initialize database
    db = Database()
    
    # Create a test project
    test_project = Project(
        title="Test Project",
        description="This is a test project",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        documents=[]
    )
    
    # Save the project
    created_project = db.create_project(test_project)
    print(f"\nCreated project with ID: {created_project.id}")
    
    # Retrieve the project
    retrieved_project = db.get_project(created_project.id)
    print(f"\nRetrieved project: {retrieved_project.dict()}")
    
    # List all projects
    all_projects = db.get_projects()
    print(f"\nAll projects ({len(all_projects)}):")
    for project in all_projects:
        print(f"- {project.title} (ID: {project.id})")

if __name__ == "__main__":
    test_project_creation() 