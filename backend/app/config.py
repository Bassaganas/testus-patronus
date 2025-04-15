from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load the appropriate .env file based on environment
env_file = BACKEND_DIR / (".env.development" if os.getenv("ENV") == "development" else ".env")
load_dotenv(env_file)

class Settings(BaseSettings):
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
    HOST: str
    PORT: int
    DEBUG: bool
    
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
    
    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_default=True
    )
    
    @property
    def origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        try:
            # Try to parse as JSON first
            import json
            return json.loads(self.ALLOWED_ORIGINS)
        except json.JSONDecodeError:
            # Fall back to comma-separated string
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def supported_document_types(self) -> List[str]:
        """Parse SUPPORTED_DOCUMENT_TYPES into a list."""
        return [doc_type.strip() for doc_type in self.SUPPORTED_DOCUMENT_TYPES.split(",")]

settings = Settings() 