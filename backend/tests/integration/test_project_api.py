import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.db.session import get_db
from app.models import Project, ProjectCreate, ProjectUpdate

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()

@pytest.fixture
def sample_project():
    return {
        "title": "Test Project",
        "description": "A test project for testing"
    }

@pytest.fixture
def sample_project_update():
    return {
        "title": "Updated Test Project",
        "description": "An updated test project"
    }

def test_create_project(client, sample_project):
    response = client.post("/api/v1/projects/", json=sample_project)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == sample_project["title"]
    assert data["description"] == sample_project["description"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_get_project(client, sample_project):
    # First create a project
    create_response = client.post("/api/v1/projects/", json=sample_project)
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["title"] == sample_project["title"]
    assert data["description"] == sample_project["description"]

def test_update_project(client, sample_project, sample_project_update):
    # First create a project
    create_response = client.post("/api/v1/projects/", json=sample_project)
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]
    
    # Then update it
    response = client.put(f"/api/v1/projects/{project_id}", json=sample_project_update)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["title"] == sample_project_update["title"]
    assert data["description"] == sample_project_update["description"]

def test_delete_project(client, sample_project):
    # First create a project
    create_response = client.post("/api/v1/projects/", json=sample_project)
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404

def test_list_projects(client, sample_project):
    # Create a project
    create_response = client.post("/api/v1/projects/", json=sample_project)
    assert create_response.status_code == 200
    
    # List all projects
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["title"] == sample_project["title"]
    assert data[0]["description"] == sample_project["description"]

@pytest.mark.integration
class TestProjectAPI:
    @pytest.mark.parametrize("invalid_data", [
        {"title": "", "description": "Test"},  # Empty title
        {"title": "Test", "description": "x" * 1001},  # Description too long
        {"title": None, "description": "Test"},  # None title
    ])
    def test_create_project_invalid_data(self, client, invalid_data):
        response = client.post("/api/v1/projects", json=invalid_data)
        assert response.status_code == 422

    def test_get_nonexistent_project(self, client):
        response = client.get("/api/v1/projects/nonexistent-id")
        assert response.status_code == 404

    def test_list_projects(self, client, sample_project):
        # Create multiple projects
        project1 = sample_project
        project2 = {**sample_project, "title": "Test Project 2"}
        
        client.post("/api/v1/projects", json=project1)
        client.post("/api/v1/projects", json=project2)
        
        # Get all projects
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(p["title"] == project1["title"] for p in data)
        assert any(p["title"] == project2["title"] for p in data) 