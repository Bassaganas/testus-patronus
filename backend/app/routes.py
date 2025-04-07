from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import os
from .document_processor import DocumentProcessor
from .vector_store import VectorStoreManager
from .rag_chain import RAGChain
from pydantic import BaseModel

router = APIRouter()

# Define the ChatRequest model to match main.py
class ChatRequest(BaseModel):
    query: str

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStoreManager()
rag_chain = RAGChain(vector_store)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document.
    """
    try:
        # Save the uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the document
        documents = document_processor.process_document(temp_path)
        
        # Add to vector store
        vector_store.add_documents(documents)
        
        # Clean up
        os.remove(temp_path)
        
        return {
            "message": "Document processed successfully",
            "chunks": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_documents(request: ChatRequest):
    """
    Query the documents using RAG.
    """
    try:
        print(f"Received query: {request.query}")
        result = rag_chain.get_response(request.query)
        print(f"Generated response: {result}")
        return {"response": result}
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_vector_store():
    """
    Reset the vector store.
    """
    try:
        vector_store.delete_collection()
        return {"message": "Vector store reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Check the health of the RAG system.
    """
    try:
        # Test vector store
        vector_store.similarity_search("test", k=1)
        
        # Test RAG chain
        rag_chain.answer_question("test")
        
        return {
            "status": "healthy",
            "components": {
                "vector_store": "operational",
                "rag_chain": "operational"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 