import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_file = BACKEND_DIR / ".env"
if not env_file.exists():
    env_file = BACKEND_DIR / ".env.development"

load_dotenv(env_file)

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# Convert SQLite URL to async format
def get_async_db_url() -> str:
    """Convert the DATABASE_URL to use aiosqlite explicitly"""
    url = DATABASE_URL
    if url.startswith('sqlite:///'):
        # Replace sqlite:/// with sqlite+aiosqlite:///
        return re.sub(r'^sqlite:', 'sqlite+aiosqlite:', url)
    return url 