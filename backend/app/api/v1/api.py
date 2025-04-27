from fastapi import APIRouter

from app.api.v1.endpoints import conversations, documents, projects, health, jira

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(jira.router, prefix="/jira", tags=["Jira"]) 