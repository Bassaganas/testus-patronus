import os
import pytest
from openai import AzureOpenAI
from app.config import settings

@pytest.fixture
def client():
    """Create an Azure OpenAI client for testing"""
    return AzureOpenAI(
        api_version=settings.AZURE_OPENAI_CHAT_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_CHAT_API_KEY,
    )

def test_azure_openai_connection(client):
    """Test the Azure OpenAI connection"""
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": "Hello! Can you confirm that the connection is working?",
                }
            ],
            max_tokens=100,
            temperature=0.7,
            top_p=1.0,
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
        )
        
        assert response.choices[0].message.content is not None
        assert len(response.choices[0].message.content) > 0
        
    except Exception as e:
        pytest.fail(f"Azure OpenAI connection failed: {str(e)}")

def test_azure_openai_embeddings():
    """Test Azure OpenAI embeddings"""
    embeddings_client = AzureOpenAI(
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_EMBEDDINGS_API_KEY,
    )
    
    try:
        response = embeddings_client.embeddings.create(
            model=settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT,
            input="Hello, world!"
        )
        
        assert response.data[0].embedding is not None
        assert len(response.data[0].embedding) > 0
        
    except Exception as e:
        pytest.fail(f"Azure OpenAI embeddings failed: {str(e)}") 