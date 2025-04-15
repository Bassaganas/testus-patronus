from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator
import re

# Convert SQLite URL to async format
def get_async_db_url() -> str:
    """Convert the DATABASE_URL to use aiosqlite explicitly"""
    url = settings.DATABASE_URL
    if url.startswith('sqlite:///'):
        # Replace sqlite:/// with sqlite+aiosqlite:///
        return re.sub(r'^sqlite:', 'sqlite+aiosqlite:', url)
    return url

# Create async engine
engine = create_async_engine(
    get_async_db_url(),
    pool_pre_ping=True,
    echo=settings.DB_ECHO
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 