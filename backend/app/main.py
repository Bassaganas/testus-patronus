from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from .routes import router
from .config import settings
from .document_processor import process_document
from .vector_store import VectorStoreManager
from .rag_chain import RAGChain
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Testus Patronus API",
    description="RAG-based API for document querying and processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize vector store
vector_store = VectorStoreManager()
rag_chain = RAGChain(vector_store)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []

# Include routes
app.include_router(router, prefix="/api/v1")

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile):
    """
    Upload and process a document.
    """
    try:
        await process_document(file, vector_store)
        return {"message": "Document processed successfully"}
    except Exception as e:
        print(f"Error processing document: {str(e)}")  # Add this line for debugging
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/query", response_model=ChatResponse)
async def query_documents(request: ChatRequest):
    try:
        response = rag_chain.get_response(request.query)
        return ChatResponse(response=response, sources=[])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reset")
async def reset_vector_store():
    try:
        vector_store.reset()
        return {"message": "Vector store reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Testus Patronus API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "vector_db": "up",  # TODO: Add actual health check
            "openai": "up"      # TODO: Add actual health check
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 