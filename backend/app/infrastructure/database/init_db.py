import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.models.project import Project
from app.infrastructure.database.models.document import Document
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.session import get_async_db_url

async def init_db():
    """
    Initialize the database by creating all tables
    """
    # Create engine
    engine = create_async_engine(get_async_db_url())
    
    # Drop all tables and recreate them
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        try:
            # Check if we need to seed the database with initial data
            result = await session.execute(text("SELECT COUNT(*) FROM projects"))
            count = result.scalar()
            if count == 0:
                # Create a default project
                default_project = Project(
                    title="Default Project",
                    description="A default project for testing"
                )
                session.add(default_project)
                await session.commit()
                print("Created default project")
        except Exception as e:
            print(f"Error seeding database: {e}")
    
    print("Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(init_db()) 