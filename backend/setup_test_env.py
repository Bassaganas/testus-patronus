#!/usr/bin/env python3
"""
Setup script for testing environment.
This script:
1. Creates necessary directories for data persistence
2. Sets up test environment variables
3. Cleans up the vector store directory if needed
"""

import os
import shutil
from pathlib import Path

# Set up paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

def setup_test_env():
    """Set up the test environment."""
    print(f"Setting up test environment in {BASE_DIR}")
    
    # Create data directory if it doesn't exist
    if not DATA_DIR.exists():
        print(f"Creating data directory: {DATA_DIR}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up vector store directory if it exists
    if VECTOR_STORE_DIR.exists():
        print(f"Cleaning up existing vector store directory: {VECTOR_STORE_DIR}")
        shutil.rmtree(VECTOR_STORE_DIR)
    
    # Create fresh vector store directory
    print(f"Creating vector store directory: {VECTOR_STORE_DIR}")
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create .env.test file with test settings
    env_test_file = BASE_DIR / ".env.test"
    print(f"Creating test environment file: {env_test_file}")
    
    env_content = f"""
# Test environment settings
VECTOR_STORE_DIR={str(VECTOR_STORE_DIR)}
DATABASE_URL=sqlite+aiosqlite:///./test.db
DB_PATH=./test.db
ALLOWED_ORIGINS=*

# Azure OpenAI settings (placeholders for testing)
AZURE_OPENAI_ENDPOINT=https://test-endpoint.openai.azure.com/
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=test-embeddings
AZURE_OPENAI_EMBEDDINGS_API_KEY=test-key
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=test-chat
AZURE_OPENAI_CHAT_API_KEY=test-key
AZURE_OPENAI_CHAT_API_VERSION=2023-05-15
"""
    
    with open(env_test_file, "w") as f:
        f.write(env_content)
    
    print("Test environment setup complete!")
    print(f"Vector store directory: {VECTOR_STORE_DIR}")
    print(f"Test environment file: {env_test_file}")

if __name__ == "__main__":
    setup_test_env() 