import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json
import logging


from app.main import app
from app.infrastructure.database.session import get_db

# Add pytest-asyncio marker to the module
pytestmark = pytest.mark.asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("testus-patronus")

# Test queries organized by category
TEST_QUERIES = {
    "project_overview": [
        "Who is working in this project?",
        "What are the main components of this project?",
        "What is the project's current status?",
        "What are the most active areas of development?",
        "What are the key milestones or deadlines?",
        "What is this project about?"
    ],
    "issue_specific": [
        "What is this issue about: {issue_key}",
        "What is the current status of {issue_key}?",
        "Who is assigned to {issue_key}?",
        "What are the dependencies for {issue_key}?",
        "What is the priority of {issue_key} and why?"
    ],
    "testing": [
        "How to test {issue_key}",
        "What are the test requirements for {issue_key}?",
        "What test cases are associated with {issue_key}?",
        "What are the known test limitations for {issue_key}?",
        "What test environments are needed for {issue_key}?"
    ],
    "quality_metrics": [
        "What are the most buggy components?",
        "Which components have the most open bugs?",
        "What is the bug resolution time for {component}?",
        "What are the most common types of bugs?",
        "Which components have the highest test coverage?"
    ],
    "regression_testing": [
        "What are the high-risk areas for regression testing?",
        "Which components are most likely to have regression issues?",
        "What changes might affect {component} testing?",
        "What are the dependencies that could cause regression issues?"
    ],
    "performance_testing": [
        "What are the performance requirements for {component}?",
        "What are the known performance bottlenecks?",
        "What performance tests are needed for {issue_key}?",
        "What are the performance acceptance criteria?"
    ],
    "integration_testing": [
        "What are the integration points for {component}?",
        "What are the integration test requirements?",
        "What are the dependencies between components?",
        "What are the integration test scenarios?"
    ],
    "release_management": [
        "What are the release criteria?",
        "What tests are needed for the next release?",
        "What are the blocking issues for release?",
        "What is the test coverage for the release?"
    ],
    "test_environment": [
        "What environments are needed for testing {component}?",
        "What are the environment-specific test requirements?",
        "What are the test data requirements?",
        "What are the environment setup instructions?"
    ],
    "test_automation": [
        "What tests should be automated?",
        "What are the automation priorities?",
        "What are the automation requirements for {issue_key}?",
        "What are the test automation dependencies?"
    ],
    "security_testing": [
        "What are the security test requirements?",
        "What security tests are needed for {component}?",
        "What are the security acceptance criteria?",
        "What are the known security vulnerabilities?"
    ],
    "documentation": [
        "What documentation is needed for testing {issue_key}?",
        "What are the test documentation requirements?",
        "What test procedures need to be documented?",
        "What are the test report requirements?"
    ]
}


@pytest.fixture(scope="module")
def client(db_session, vector_store_manager):
    """Create a test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Import and override vector store dependency to use our fixture
    from app.core.dependencies import get_vector_store_manager
    
    def override_vector_store():
        return vector_store_manager
    
    app.dependency_overrides[get_vector_store_manager] = override_vector_store
    
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def first_issue_key(client, setup_project_and_conversation):
    project_id, _ = setup_project_and_conversation
    response = client.get(f"/api/v1/documents/", params={"project_id": project_id})
    assert response.status_code == 200
    documents = response.json()
    jira_issues = [
        doc for doc in documents
        if doc.get("source_type") == "jira" and doc.get("doc_metadata", {}).get("document_type") != "project_summary"
    ]
    if not jira_issues:
        pytest.skip("No Jira issues found to test with")
    return jira_issues[0].get("doc_metadata", {}).get("issue_key", "UNKNOWN")


@pytest.fixture(scope="module")
def setup_project_and_conversation(client):
    # Create project
    response = client.post(
        "/api/v1/projects/",
        json={"title": "Test Project", "description": "A test project for RAG queries"}
    )
    assert response.status_code == 200
    project_id = response.json()["id"]
    
    # Get available project_keys from the /files endpoint
    response = client.get("/api/v1/jira/files")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
    project_key = projects[1]["project_key"]
    assert project_key

    # Import Jira data
    response = client.post(
        "/api/v1/jira/import",
        params={
            "project_key": project_key,
            "timestamp": "20250427_225549",
            "project_id": project_id
        }
    )
    assert response.status_code == 200

    # Wait for vector store to process
    import time
    time.sleep(2)

    # Create conversation
    response = client.post(
        "/api/v1/conversations/",
        json={
            "title": "Test Conversation",
            "project_id": project_id
        }
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    return project_id, conversation_id


@pytest.mark.parametrize("query", TEST_QUERIES["project_overview"])
def test_project_overview_queries(client, setup_project_and_conversation, query):
    _, conversation_id = setup_project_and_conversation

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/query",
        json={"query": query}
    )

    data = response.json()
    logger.info("Query: {query}, and Response: {data}")
    assert response.status_code == 200


@pytest.mark.parametrize("query", TEST_QUERIES["issue_specific"])
def test_project_issue_specific_queries(client, setup_project_and_conversation,first_issue_key, query):
    _, conversation_id = setup_project_and_conversation
    # Format the query with the actual issue key
    formatted_query = query.format(issue_key=first_issue_key)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/query",
        json={"query": formatted_query}
    )

    data = response.json()
    logger.info(f"Query: {formatted_query}, and Response: {data}")
    assert response.status_code == 200


 