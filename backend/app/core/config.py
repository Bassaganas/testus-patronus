from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logger = logging.getLogger("testus-patronus")

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load the appropriate .env file based on environment
env_file = BACKEND_DIR / (".env.development" if os.getenv("ENV") == "development" else ".env")
logger.info(f"Loading environment from: {env_file}")
load_dotenv(env_file)

# Log environment variables
logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
logger.info(f"DB_PATH: {os.getenv('DB_PATH')}")
logger.info(f"ALLOWED_ORIGINS: {os.getenv('ALLOWED_ORIGINS')}")

VECTOR_STORE_DIR = os.getenv(
    "VECTOR_STORE_DIR",
    str(BACKEND_DIR / "data" / "vector_store")
)

class Settings(BaseSettings):
    # Project Information
    PROJECT_NAME: str = "Testus Patronus"
    VERSION: str = "1.0.0"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str
    
    # Embeddings Configuration
    AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT: str
    AZURE_OPENAI_EMBEDDINGS_API_KEY: str
    AZURE_OPENAI_API_VERSION: str
    
    # Chat Configuration
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME: str
    AZURE_OPENAI_CHAT_API_KEY: str
    AZURE_OPENAI_CHAT_API_VERSION: str
    
    # Vector Store Configuration
    VECTOR_STORE_DIR: str
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Configuration
    ALLOWED_ORIGINS: str
    
    # Additional Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    MAX_TOKENS: int = 1000
    MAX_DOCUMENT_SIZE_MB: int = 10
    SUPPORTED_DOCUMENT_TYPES: str = "pdf,txt,md,html"
    
    # DB Settings
    DB_PATH: str
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_default=True
    )

settings = Settings() 