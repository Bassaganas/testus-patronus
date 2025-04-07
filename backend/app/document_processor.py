from typing import List, Dict, Any, Type
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)
from langchain.schema import Document
import os
from .config import settings
from .vector_store import VectorStoreManager
from fastapi import UploadFile, HTTPException
import tempfile
import shutil

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        
        self.loader_map = {
            "pdf": PyPDFLoader,
            "txt": TextLoader,
            "md": UnstructuredMarkdownLoader,
            "html": UnstructuredHTMLLoader
        }
    
    def process_document(self, file_path: str) -> List[Document]:
        """
        Process a document and return a list of Document objects.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        file_extension = file_path.split(".")[-1].lower()
        
        if file_extension not in settings.SUPPORTED_DOCUMENT_TYPES:
            raise ValueError(f"Unsupported document type: {file_extension}")
            
        # Get the appropriate loader
        loader_class = self.loader_map.get(file_extension)
        if not loader_class:
            raise ValueError(f"No loader found for {file_extension}")
            
        # Load and split the document
        loader = loader_class(file_path)
        documents = loader.load()
        split_docs = self.text_splitter.split_documents(documents)
        
        return split_docs
    
    def process_directory(self, directory_path: str) -> List[Document]:
        """
        Process all supported documents in a directory.
        
        Args:
            directory_path: Path to the directory containing documents
            
        Returns:
            List of Document objects
        """
        all_documents = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_extension = file.split(".")[-1].lower()
                if file_extension in settings.SUPPORTED_DOCUMENT_TYPES:
                    file_path = os.path.join(root, file)
                    try:
                        documents = this.process_document(file_path)
                        all_documents.extend(documents)
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")
                        
        return all_documents 

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

async def process_document(file: UploadFile, vector_store: VectorStoreManager) -> None:
    """
    Process an uploaded document and add it to the vector store.
    
    Args:
        file (UploadFile): The uploaded file
        vector_store (VectorStoreManager): The vector store manager instance
    
    Raises:
        HTTPException: If the file type is not supported or processing fails
    """
    # Get file extension
    file_extension = file.filename.split(".")[-1].lower()
    
    # Check if file type is supported
    if file_extension not in settings.SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types are: {settings.SUPPORTED_DOCUMENT_TYPES}"
        )
    
    # Check file size
    file_size = 0
    content = bytearray()
    
    # Read file in chunks to check size
    while chunk := await file.read(8192):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"
            )
        content.extend(chunk)
    
    # Reset file position
    await file.seek(0)
    
    try:
        # Create a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            # Write the content to the temporary file
            temp_file.write(content)
            temp_file.flush()
            
            print(f"Processing file: {file.filename} (size: {file_size/1024/1024:.2f}MB)")
            
            # Get appropriate loader
            loader_class = LOADER_MAP.get(file_extension)
            if not loader_class:
                raise HTTPException(
                    status_code=400,
                    detail=f"No loader found for file type: {file_extension}"
                )
            
            # Load the document
            loader = loader_class(temp_file.name)
            documents = loader.load()
            
            print(f"Loaded {len(documents)} documents")
            
            # Add documents to vector store
            vector_store.add_documents(documents)
            print("Documents added to vector store")
            
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file.name)
        except Exception as e:
            print(f"Error cleaning up temporary file: {str(e)}")

# Map file extensions to their respective document loaders
LOADER_MAP: Dict[str, Type] = {
    "pdf": PyPDFLoader,
    "txt": TextLoader,
    "md": UnstructuredMarkdownLoader,
    "html": UnstructuredHTMLLoader,
} 