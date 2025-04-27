import pytest
import asyncio
import os
import shutil
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.project import Project
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Get the absolute path to the tests directory
    TESTS_DIR = Path(__file__).resolve().parent.parent
    INTEGRATION_DIR = TESTS_DIR / "integration"
    
    # Load integration environment variables first
    load_dotenv(dotenv_path=INTEGRATION_DIR / ".env.integration", override=True)
    
    # Create test_data directory structure
    TEST_DATA_DIR = TESTS_DIR / "test_data"
    DB_DIR = TEST_DATA_DIR / "db"
    VECTOR_STORE_DIR = TEST_DATA_DIR / "vector_store"
    
    # Create directories if they don't exist
    DB_DIR.mkdir(parents=True, exist_ok=True)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verify required environment variables are set
    required_vars = [
        "DATABASE_URL",
        "DB_PATH",
        "VECTOR_STORE_DIR",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT",
        "AZURE_OPENAI_EMBEDDINGS_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME",
        "AZURE_OPENAI_CHAT_API_KEY",
        "AZURE_OPENAI_CHAT_API_VERSION",
        "ALLOWED_ORIGINS"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables for testing: {', '.join(missing_vars)}\n"
            "Please ensure all required variables are set in .env.integration file."
        )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    # Get the absolute path to the tests directory
    TESTS_DIR = Path(__file__).resolve().parent.parent
    TEST_DATA_DIR = TESTS_DIR / "test_data"
    DB_DIR = TEST_DATA_DIR / "db"
    
    # Ensure the database directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use database URL from environment
    test_db_url = os.getenv("DATABASE_URL")
    
    # Ensure we're using the async SQLite driver
    if not test_db_url.startswith("sqlite+aiosqlite"):
        test_db_url = test_db_url.replace("sqlite://", "sqlite+aiosqlite://")
        print(f"Updated database URL to use async driver: {test_db_url}")
    
    engine = create_async_engine(test_db_url, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        # Create a default project for testing with a valid UUID
        try:
            test_project_id = str(uuid.uuid4())
            await conn.execute(text("""
                INSERT INTO projects (id, title, description, created_at, updated_at)
                VALUES (:id, 'Test Project', 'A project for integration tests', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {"id": test_project_id})
        except Exception as e:
            print(f"Error creating default project: {e}")
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="module")
async def db_session(test_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Clean up test data before and after tests."""
    # Get paths from environment variables
    TESTS_DIR = Path(__file__).resolve().parent.parent
    TEST_DATA_DIR = TESTS_DIR / "test_data"
    DB_DIR = TEST_DATA_DIR / "db"
    VECTOR_STORE_DIR = TEST_DATA_DIR / "vector_store"
    
    # Clean up before tests
    if VECTOR_STORE_DIR.exists():
        shutil.rmtree(VECTOR_STORE_DIR)
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    
    if DB_DIR.exists():
        for file in DB_DIR.glob("*.db"):
            file.unlink()
    
    yield
    
    # Clean up after tests
    if VECTOR_STORE_DIR.exists():
        shutil.rmtree(VECTOR_STORE_DIR)
    if DB_DIR.exists():
        for file in DB_DIR.glob("*.db"):
            file.unlink()

@pytest.fixture(scope="module")
def vector_store_manager():
    """Get a VectorStoreManager instance for testing using integration environment."""
    manager = VectorStoreManager()
    manager.reset()  # Clean state before tests
    yield manager
    manager.reset()  # Clean up after tests 