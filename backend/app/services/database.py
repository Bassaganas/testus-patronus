from app.repositories import DocumentRepository, ConversationRepository, ProjectRepository
from app.db.session import SessionLocal
import logging

logger = logging.getLogger("testus-patronus")

class DatabaseService:
    def __init__(self):
        self.db = SessionLocal()
        self.documents = DocumentRepository(self.db)
        self.conversations = ConversationRepository(self.db)
        self.projects = ProjectRepository(self.db)
        logger.info("Database service initialized with SQLAlchemy session")

    def __del__(self):
        """Close the database session when the service is destroyed."""
        if hasattr(self, 'db'):
            self.db.close()

# Create a singleton instance
db = DatabaseService() 