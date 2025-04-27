import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.database.session import get_db
import uuid
import os
from pathlib import Path
import json
import asyncio
from typing import Generator

@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with the database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_project(client) -> str:
    """Create a test project and return its ID."""
    project_id = str(uuid.uuid4())
    response = client.post(
        "/api/v1/projects/",
        json={
            "id": project_id,
            "title": "Test Project",
            "description": "A project for testing"
        }
    )
    assert response.status_code == 200
    return project_id

@pytest.fixture
def test_data_dir() -> Path:
    """Create and return the test data directory."""
    test_dir = Path(__file__).parent.parent / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

@pytest.mark.asyncio
async def test_import_jira_data(client, test_project):
    """Test importing Jira data by project_key."""
    # Get available project_keys from the /files endpoint
    response = client.get("/api/v1/jira/files")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
    # Pick the first available project_key
    project_key = projects[0]["project_key"]
    assert project_key

    response = client.post(
        "/api/v1/jira/import",
        params={
            "project_key": project_key,
            "timestamp": "latest",
            "project_id": test_project
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Jira project imported successfully"
    # Wait for vector store to process documents
    await asyncio.sleep(2)
    # Verify documents were stored in vector store
    response = client.get(f"/api/v1/documents/{test_project}/vector")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # Verify document content
    doc = data[0]
    assert "content" in doc
    assert "metadata" in doc
    assert doc["metadata"]["project_id"] == test_project
    assert doc["metadata"]["source_type"] == "jira"
    # Verify documents were stored in the backend database
    response = client.get(f"/api/v1/documents?project_id={test_project}")
    assert response.status_code == 200
    db_docs = response.json()
    assert len(db_docs) > 0
    assert any(doc["project_id"] == test_project for doc in db_docs)

@pytest.mark.asyncio
async def test_get_document_from_vector_store(client, test_project):
    """Test retrieving a document from the vector store by project_key."""
    # Get available project_keys from the /files endpoint
    response = client.get("/api/v1/jira/files")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
    project_key = projects[0]["project_key"]
    assert project_key
    # Import data for the project_key
    response = client.post(
        "/api/v1/jira/import",
        params={
            "project_key": project_key,
            "timestamp": "latest",
            "project_id": test_project
        }
    )
    assert response.status_code == 200
    # Wait for vector store to process documents
    await asyncio.sleep(2)
    # Get a document_id for this project_key (simulate by using the first doc)
    response = client.get(f"/api/v1/documents/{test_project}/vector")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    doc = data[0]
    document_id = doc["metadata"].get("document_id")
    assert document_id
    # Get document from vector store
    response = client.get(f"/api/v1/documents/{document_id}/vector")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    doc = data[0]
    assert "content" in doc
    assert "metadata" in doc
    assert doc["metadata"]["document_id"] == document_id

@pytest.mark.asyncio
async def test_get_nonexistent_document(client):
    """Test retrieving a nonexistent document."""
    nonexistent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/documents/{nonexistent_id}/vector")
    assert response.status_code == 404
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_import_jira_data_with_invalid_json(client, test_project, test_data_dir):
    """Test importing invalid Jira JSON data (should fail)."""
    # This test is now less relevant, but we can simulate by passing a non-existent project_key
    response = client.post(
        "/api/v1/jira/import",
        params={
            "project_key": "NONEXISTENTKEY",
            "timestamp": "latest",
            "project_id": test_project
        }
    )
    assert response.status_code == 400 or response.status_code == 422
    assert "detail" in response.json()

