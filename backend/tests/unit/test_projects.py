import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from app.models import Project, ProjectCreate, ProjectUpdate
from app.repositories.project import ProjectRepository
from app.services.project_service import ProjectService
from app.api.v1.exceptions import NotFoundError, ValidationError
from app.vector_store import VectorStoreManager
from fastapi import HTTPException

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_vector_store():
    return Mock(spec=VectorStoreManager)

@pytest.fixture
def project_repository(mock_db):
    return ProjectRepository(mock_db)

@pytest.fixture
def project_service(mock_db, mock_vector_store):
    return ProjectService(vector_store=mock_vector_store, db=mock_db)

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
    @pytest.mark.asyncio
    async def test_create_project(self, project_service, mock_db, sample_project_data):
        # Arrange
        project_create = ProjectCreate(
            title=sample_project_data["title"],
            description=sample_project_data["description"]
        )
        # Mock the repository's create method
        project_service.repository.create = Mock(return_value=Project(**sample_project_data))
        
        # Act
        result = await project_service.create_project(project_create)
        
        # Assert
        assert result.title == sample_project_data["title"]
        assert result.description == sample_project_data["description"]
        project_service.repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_service, mock_db):
        # Arrange
        project_service.repository.get_by_id = Mock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            await project_service.get_project("non-existent-id")
        assert excinfo.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, project_service, mock_db, sample_project):
        # Arrange
        project_service.repository.get_by_id = Mock(return_value=sample_project)
        updated_project = Project(
            id=sample_project.id,
            title="Updated Title",
            description="Updated description",
            created_at=sample_project.created_at,
            updated_at=datetime.utcnow(),
            documents=[]
        )
        project_service.repository.update = Mock(return_value=updated_project)
        update_data = ProjectUpdate(
            title="Updated Title",
            description="Updated description"
        )
        
        # Act
        result = await project_service.update_project(sample_project.id, update_data)
        
        # Assert
        assert result.title == "Updated Title"
        assert result.description == "Updated description"
        project_service.repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project(self, project_service, mock_db, sample_project):
        # Arrange
        project_service.repository.get_by_id = Mock(return_value=sample_project)
        project_service.repository.delete = Mock(return_value=True)
        
        # Act
        result = await project_service.delete_project(sample_project.id)
        
        # Assert
        assert result is None
        project_service.repository.delete.assert_called_once() 