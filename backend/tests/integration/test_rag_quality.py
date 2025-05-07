import pytest
import httpx
from httpx import AsyncClient, ASGITransport
import json
import logging
import time
from typing import Dict, List, Any
from textwrap import dedent

from app.main import app
from app.infrastructure.database.session import get_db

# Add pytest-asyncio marker to the module
pytestmark = pytest.mark.asyncio

# Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("testus-patronus")

# Test data for RAG quality tests
RAG_QUALITY_TEST_CASES = {
    "empty_answer_tests": [
        {
            "query": "What is the meaning of life?",
            "expected_keywords": ["meaning", "life"],
            "should_be_empty": True
        },
        {
            "query": "Tell me about quantum physics",
            "expected_keywords": ["quantum", "physics"],
            "should_be_empty": True
        }
    ],
    "no_information_tests": [
        {
            "query": "What is the status of issue ABC-123?",
            "expected_response": ["no information", "cannot find", "don't have information"],
            "should_indicate_no_info": True
        },
        {
            "query": "What are the test results for XYZ-789?",
            "expected_response": ["no information", "cannot find", "don't have information"],
            "should_indicate_no_info": True
        }
    ],
    "advanced_testing_queries": [
        {
            "query": "Which issues propose improvements that could break backward compatibility?",
            "expected_keywords": ["backward", "breaking", "incompatible", "major version"],
        },
        {
            "query": "Which new features need extensive regression testing?",
            "expected_keywords": ["new feature", "regression", "testing"],
        },
        {
            "query": "Are there any tasks that mention 'feature toggles' or 'configuration' options that need testing in both enabled and disabled states?",
            "expected_keywords": ["feature toggle", "configuration", "enable", "disable"],
        },
        {
            "query": "Which issues are marked as 'Bugs' and what are their impact areas?",
            "expected_keywords": ["bug", "impact"],
        },
        {
            "query": "Which issues reference problems with CORS, WADL schemas, or REST API inconsistencies?",
            "expected_keywords": ["cors", "schema", "rest api", "inconsistency"],
        },
        {
            "query": "Which improvements relate to performance optimization?",
            "expected_keywords": ["performance", "optimization", "improvement"],
        },
        {
            "query": "What tasks involve documentation improvements or deficiencies?",
            "expected_keywords": ["documentation", "example", "improvement"],
        },
        {
            "query": "Which changes could affect multiple products like JIRA, Confluence, Bitbucket?",
            "expected_keywords": ["jira", "confluence", "bitbucket"],
        }
    ]
}

def format_test_result(test_name: str, query: str, response: str, expected: Dict[str, Any], actual: Dict[str, Any]) -> str:
    result = dedent(f"""
    {'='*80}
    Test: {test_name}
    {'='*80}
    
    Query:
    {query}
    
    Response:
    {response}
    
    Expected:
    {json.dumps(expected, indent=2)}
    
    Actual:
    {json.dumps(actual, indent=2)}
    
    {'='*80}
    """)
    return result

def analyze_keyword_matches(text: str, keywords: List[str]) -> Dict[str, bool]:
    text_lower = text.lower()
    return {keyword: keyword.lower() in text_lower for keyword in keywords}

def is_empty_response(response: Dict[str, Any]) -> bool:
    if not response:
        return True
    answer = response.strip()
    return len(answer) < 20

def indicates_no_information(response: Dict[str, Any], expected_phrases: List[str]) -> bool:
    if not response:
        return False
    answer = response.lower()
    return any(phrase.lower() in answer for phrase in expected_phrases)


@pytest.fixture(scope="module")
async def client(db_session, vector_store_manager):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from app.core.dependencies import get_vector_store_manager

    def override_vector_store():
        return vector_store_manager

    app.dependency_overrides[get_vector_store_manager] = override_vector_store

    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True, transport=ASGITransport(app=app)) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
async def setup_project_and_conversation(client):
    response = await client.post("/api/v1/projects/", json={"title": "RAG Quality Test Project", "description": "A test project for RAG quality tests"})
    assert response.status_code == 200
    project_id = response.json()["id"]

    response = await client.get("/api/v1/jira/files/")
    assert response.status_code == 200
    projects = response.json()
    project_key = projects[0]["project_key"]
    assert project_key

    response = await client.post(
        "/api/v1/jira/import",
        params={"project_key": project_key, "timestamp": "latest", "project_id": project_id}
    )
    assert response.status_code == 200

    time.sleep(2)

    response = await client.post("/api/v1/conversations/", json={"title": "RAG Quality Test Conversation", "project_id": project_id})
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    return project_id, conversation_id

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", RAG_QUALITY_TEST_CASES["empty_answer_tests"])
async def test_empty_answer_handling(client, setup_project_and_conversation, test_case):
    _, conversation_id = setup_project_and_conversation
    response = await client.post(f"/api/v1/conversations/{conversation_id}/query", json={"query": test_case["query"]})
    assert response.status_code == 200
    answer = response.json()

    test_result = format_test_result("Empty Answer Test", test_case["query"], answer, {"should_be_empty": test_case["should_be_empty"]}, {"is_empty": is_empty_response(answer)})
    logger.info(test_result)
    assert is_empty_response(answer) == test_case["should_be_empty"]

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", RAG_QUALITY_TEST_CASES["no_information_tests"])
async def test_no_information_handling(client, setup_project_and_conversation, test_case):
    _, conversation_id = setup_project_and_conversation
    response = await client.post(f"/api/v1/conversations/{conversation_id}/query", json={"query": test_case["query"]})
    assert response.status_code == 200
    answer = response.json()

    test_result = format_test_result("No Information Test", test_case["query"], answer, {"should_indicate_no_info": test_case["should_indicate_no_info"], "expected_phrases": test_case["expected_response"]}, {"indicates_no_info": indicates_no_information(answer, test_case["expected_response"]), "found_phrases": [phrase for phrase in test_case["expected_response"] if phrase.lower() in answer.lower()]})
    logger.info(test_result)
    assert indicates_no_information(answer, test_case["expected_response"]) == test_case["should_indicate_no_info"]

@pytest.mark.advanced
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", RAG_QUALITY_TEST_CASES["advanced_testing_queries"])
async def test_advanced_quality_queries(client, setup_project_and_conversation, test_case):
    _, conversation_id = setup_project_and_conversation
    response = await client.post(f"/api/v1/conversations/{conversation_id}/query", json={"query": test_case["query"]})
    assert response.status_code == 200
    answer = response.json()

    keyword_matches = analyze_keyword_matches(answer, test_case["expected_keywords"])
    word_count = len(answer.split())

    test_result = format_test_result("Advanced Quality Test", test_case["query"], answer, {"min_word_count": 20, "expected_keywords": test_case["expected_keywords"]}, {"word_count": word_count, "keyword_matches": keyword_matches, "missing_keywords": [k for k, v in keyword_matches.items() if not v]})
    logger.info(test_result)

    assert answer
    assert word_count > 20
    if "expected_keywords" in test_case:
        keywords_found = any(keyword_matches.values())
        assert keywords_found
