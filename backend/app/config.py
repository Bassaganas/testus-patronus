from typing import List
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str  # For chat completion
    AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT: str = "text-embedding-ada-002"  # For embeddings
    AZURE_OPENAI_API_VERSION: str
    MAX_TOKENS: int = 1000

    # Vector Store Configuration
    VECTOR_STORE_PATH: str

    # Server Configuration
    HOST: str
    PORT: int
    DEBUG: bool

    # CORS Configuration
    ALLOWED_ORIGINS: List[str]

    # Vector DB Settings
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma"
    
    # Document Processing Settings
    SUPPORTED_DOCUMENT_TYPES: list = ["pdf", "txt", "md", "html"]
    MAX_DOCUMENT_SIZE_MB: int = 10
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings() 