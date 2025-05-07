import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models.conversation import Conversation as DBConversation
from app.domain.models.conversation import Conversation as DomainConversation

# Add pytest-asyncio marker to the module
pytestmark = pytest.mark.asyncio

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
def sample_project(client):
    """Create a sample project for testing conversations"""
    project_data = {
        "title": "Test Project",
        "description": "A test project for conversation testing"
    }
    response = client.post("/api/v1/projects/", json=project_data)
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def sample_conversation():
    """Sample conversation data for testing"""
    return {
        "title": "Test Conversation",
        "messages": []
    }

@pytest.fixture
def sample_message():
    """Sample message data for testing"""
    return {
        "role": "user",
        "content": "Hello, this is a test message"
    }

@pytest.mark.integration
class TestConversationAPI:
    def test_create_conversation(self, client, sample_conversation, sample_project):
        """Test creating a new conversation"""
        # Create conversation with project
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        response = client.post("/api/v1/conversations/", json=conversation_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == conversation_data["title"]
        assert data["project_id"] == sample_project["id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0

    def test_get_conversation(self, client, sample_conversation, sample_project):
        """Test retrieving a conversation by ID"""
        # First create a conversation
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        create_response = client.post("/api/v1/conversations/", json=conversation_data)
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/v1/conversations/{conversation_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == conversation_data["title"]
        assert data["project_id"] == sample_project["id"]

    def test_update_conversation(self, client, sample_conversation, sample_project):
        """Test updating a conversation"""
        # First create a conversation
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        create_response = client.post("/api/v1/conversations/", json=conversation_data)
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Then update it
        update_data = {"title": "Updated Test Conversation"}
        response = client.put(f"/api/v1/conversations/{conversation_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == update_data["title"]
        assert data["project_id"] == sample_project["id"]

    def test_delete_conversation(self, client, sample_conversation, sample_project):
        """Test deleting a conversation"""
        # First create a conversation
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        create_response = client.post("/api/v1/conversations/", json=conversation_data)
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Then delete it
        response = client.delete(f"/api/v1/conversations/{conversation_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/conversations/{conversation_id}")
        assert get_response.status_code == 404

    def test_list_conversations(self, client, sample_conversation, sample_project):
        """Test listing all conversations"""
        # Clean up any existing conversations
        response = client.get("/api/v1/conversations")
        existing_conversations = response.json()
        for conv in existing_conversations:
            client.delete(f"/api/v1/conversations/{conv['id']}")
        
        # Create multiple conversations
        conversation1 = {**sample_conversation, "project_id": sample_project["id"]}
        conversation2 = {
            **sample_conversation,
            "title": "Test Conversation 2",
            "project_id": sample_project["id"]
        }
        
        client.post("/api/v1/conversations/", json=conversation1)
        client.post("/api/v1/conversations/", json=conversation2)
        
        # List all conversations
        response = client.get("/api/v1/conversations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(c["title"] == conversation1["title"] for c in data)
        assert any(c["title"] == conversation2["title"] for c in data)

        # Test filtering by project_id
        response = client.get(f"/api/v1/conversations?project_id={sample_project['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(c["project_id"] == sample_project["id"] for c in data)

    def test_add_message(self, client, sample_conversation, sample_project, sample_message):
        """Test adding a message to a conversation"""
        # Create a conversation
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        create_response = client.post("/api/v1/conversations/", json=conversation_data)
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Add a message
        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json=sample_message
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify the message was added correctly
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == sample_message["role"]
        assert data["messages"][0]["content"] == sample_message["content"]
        
        # Verify by getting the conversation
        get_response = client.get(f"/api/v1/conversations/{conversation_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert len(get_data["messages"]) == 1
        assert get_data["messages"][0]["role"] == sample_message["role"]
        assert get_data["messages"][0]["content"] == sample_message["content"]

    def test_get_nonexistent_conversation(self, client):
        """Test getting a nonexistent conversation"""
        nonexistent_id = str(uuid4())
        response = client.get(f"/api/v1/conversations/{nonexistent_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("invalid_data", [
        {"role": "", "content": "Test message"},  # Empty role
        {"role": "invalid_role", "content": "Test message"},  # Invalid role
        {"role": "user", "content": ""},  # Empty content
        {"role": None, "content": "Test message"},  # None role
        {"role": "user", "content": None},  # None content
    ])
    def test_add_message_invalid_data(self, client, sample_conversation, sample_project, invalid_data):
        """Test adding a message with invalid data"""
        # Create a conversation first
        conversation_data = {**sample_conversation, "project_id": sample_project["id"]}
        create_response = client.post("/api/v1/conversations/", json=conversation_data)
        assert create_response.status_code == 200
        conversation_id = create_response.json()["id"]
        
        # Try to add invalid message
        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json=invalid_data
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_data", [
        {"title": "", "project_id": str(uuid4())},  # Empty title
        {"title": None, "project_id": str(uuid4())},  # None title
        {"title": "Test", "project_id": "invalid-uuid"},  # Invalid UUID
    ])
    def test_create_conversation_invalid_data(self, client, invalid_data):
        """Test creating a conversation with invalid data"""
        response = client.post("/api/v1/conversations/", json=invalid_data)
        assert response.status_code == 422 