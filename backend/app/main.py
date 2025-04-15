import logging
import os

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.infrastructure.database.init_db import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("testus-patronus")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG-based API for document querying and processing",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router)

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that runs when the application starts.
    """
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    
    # Harry Potter style ASCII art
    ascii_art = """
    \033[1;33m
     _____         _                ____       _                           
    |_   _|__  ___| |_ _   _ ___  |  _ \ __ _| |_ _ __ ___  _ __  _   _ ___
      | |/ _ \/ __| __| | | / __| | |_) / _` | __| '__/ _ \| '_ \| | | / __|
      | |  __/\__ \ |_| |_| \__ \ |  __/ (_| | |_| | | (_) | | | | |_| \__ \\
      |_|\___||___/\__|\__,_|___/ |_|   \__,_|\__|_|  \___/|_| |_|\__,_|___/
                                                    
    \033[0m"""
    
    print(ascii_art)
    print("\n" + "✨" * 25)
    print("\033[1;36m" + "Welcome to the Document Processing API!" + "\033[0m")
    print("✨" * 25 + "\n")

    # Get Codespaces URL if available
    codespace_name = os.getenv("CODESPACE_NAME")
    base_url = f"https://{codespace_name}-8000.app.github.dev" if codespace_name else "http://0.0.0.0:8000"
    
    print("\033[1;32m" + "API URLs:" + "\033[0m")
    print(f"📡 Main API:     {base_url}")
    print(f"📚 Swagger UI:   {base_url}/docs")
    print(f"📖 ReDoc:        {base_url}/redoc")
    print(f"🔍 OpenAPI:     {base_url}/openapi.json")
    
    print("\n" + "=" * 50)
    print("\033[1;33m" + "Ready to process your documents! 📄 ✨" + "\033[0m")
    print("=" * 50 + "\n")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
        "status": "operational",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 