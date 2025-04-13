from typing import List, Dict, Any, Optional, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)
from langchain_core.documents import Document as LangchainDocument
from .models import Document
from .services.database import db
from .config import settings
from .vector_store import VectorStoreManager
from fastapi import UploadFile, HTTPException
import tempfile
import os
import logging
from datetime import datetime
from uuid import uuid4
from pathlib import Path

# Get logger
logger = logging.getLogger("testus-patronus")

class DocumentProcessor:
    def __init__(self):
        """Initialize the document processor with text splitter and loader configuration."""
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
    
    def _validate_file_type(self, file_name: str) -> str:
        """Validate file type and return the extension."""
        file_extension = file_name.split(".")[-1].lower()
        if file_extension not in settings.SUPPORTED_DOCUMENT_TYPES:
            raise ValueError(f"Unsupported document type: {file_extension}")
        return file_extension
    
    def _get_loader(self, file_extension: str):
        """Get the appropriate document loader for the file type."""
        loader_class = self.loader_map.get(file_extension)
        if not loader_class:
            raise ValueError(f"No loader found for {file_extension}")
        return loader_class
    
    def _process_file(self, file_path: str) -> List[LangchainDocument]:
        """Process a file and return a list of document chunks."""
        file_extension = self._validate_file_type(file_path)
        loader_class = self._get_loader(file_extension)
        
        loader = loader_class(file_path)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)
    
    def process_directory(self, directory_path: str) -> List[LangchainDocument]:
        """Process all supported documents in a directory."""
        all_documents = []
        
        for file_path in Path(directory_path).rglob("*"):
            if file_path.is_file():
                try:
                    file_extension = self._validate_file_type(file_path.name)
                    documents = self._process_file(str(file_path))
                    all_documents.extend(documents)
                except ValueError as e:
                    logger.warning(f"Skipping {file_path}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    
        return all_documents

    async def process_upload(
        self,
        file: UploadFile,
        vector_store: VectorStoreManager,
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Document:
        """Process an uploaded document."""
        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {settings.MAX_DOCUMENT_SIZE_MB}MB"
            )
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            try:
                # Write content to temporary file
                temp_file.write(content)
                temp_file.flush()
                
                # Process the document
                split_docs = self._process_file(temp_file.name)
                
                # Create document metadata
                doc_id = str(uuid4())
                metadata = {
                    "file_name": file.filename,
                    "file_type": self._validate_file_type(file.filename),
                    "file_size": len(content),
                    "chunk_count": len(split_docs),
                    "conversation_id": conversation_id,
                    "project_id": project_id
                }
                
                # Add vectors to vector store
                vector_store.add_documents(split_docs, doc_id)
                
                # Create document record
                document = Document(
                    id=doc_id,
                    title=file.filename,
                    file_name=file.filename,
                    file_type=metadata["file_type"],
                    file_size=len(content),
                    content="\n".join([doc.page_content for doc in split_docs]),
                    doc_metadata=metadata,
                    project_id=project_id,
                    conversation_id=conversation_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                return document
                
            finally:
                # Clean up the temporary file
                os.unlink(temp_file.name)

def get_document_content(document_id: str) -> List[LangchainDocument]:
    """Retrieve the content of a document from the vector store."""
    document = db.documents.get_by_id(document_id)
    if not document:
        return []
    
    vector_store = VectorStoreManager()
    return vector_store.get_document(document_id) 