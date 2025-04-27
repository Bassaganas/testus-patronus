from typing import List, Dict, Any, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)
from langchain_core.documents import Document as LangchainDocument
from .db.models import Document
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
import time

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
        if file_extension not in settings.supported_document_types:
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
        try:
            # Get file extension from path
            file_extension = os.path.splitext(file_path)[1].lower().lstrip('.')
            logger.info(f"Processing file with extension: {file_extension}")
            
            # Validate file type
            if file_extension not in settings.supported_document_types:
                logger.error(f"Unsupported document type: {file_extension}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported document type: {file_extension}"
                )
            
            # Get the appropriate loader for the file type
            loader_class = self._get_loader(file_extension)
            logger.info(f"Using loader class: {loader_class.__name__}")
            
            # Load and process the document
            loader = loader_class(file_path)
            logger.info(f"Loading document from: {file_path}")
            documents = loader.load()
            logger.info(f"Document loaded successfully, splitting into chunks")
            
            # Split documents into chunks
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"Document split into {len(split_docs)} chunks")
            
            return split_docs
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )
    
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
        db_session,
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """Process an uploaded document and store it in both the vector store and backend DB."""
        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {settings.MAX_DOCUMENT_SIZE_MB}MB"
            )
        file_extension = self._validate_file_type(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            try:
                temp_file.write(content)
                temp_file.flush()
                split_docs = self._process_file(temp_file.name)
                doc_id = str(uuid4())
                metadata = {
                    "file_name": file.filename,
                    "file_type": file_extension,
                    "file_size": len(content),
                    "chunk_count": len(split_docs),
                    "conversation_id": conversation_id,
                    "project_id": project_id
                }
                max_retries = 3
                retry_delay = 2
                last_error = None
                for attempt in range(max_retries):
                    try:
                        vector_store.add_documents(
                            split_docs, 
                            doc_id, 
                            project_id=project_id, 
                            conversation_id=conversation_id
                        )
                        break
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Attempt {attempt+1}/{max_retries} to add documents to vector store failed: {str(e)}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                if last_error:
                    logger.warning(f"All attempts to add documents to vector store failed. Creating document without vectors.")
                    logger.warning(f"Last error: {str(last_error)}")
                # --- Store in backend DB ---
                from app.infrastructure.repositories.document_repository import DocumentRepository
                from app.domain.schemas.document import DocumentCreate
                document_create = DocumentCreate(
                    title=file.filename,
                    source_type="file",  # or set appropriately
                    source_id=doc_id,
                    file_name=file.filename,
                    file_type=file_extension,
                    file_size=len(content),
                    content="\n".join([doc.page_content for doc in split_docs]),
                    doc_metadata=metadata,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                repo = DocumentRepository(db_session)
                db_document = await repo.create(document_create)
                return db_document
            finally:
                os.unlink(temp_file.name)

def get_document_content(document_id: str) -> List[LangchainDocument]:
    """Retrieve the content of a document from the vector store."""
    document = db.documents.get_by_id(document_id)
    if not document:
        return []
    
    vector_store = VectorStoreManager()
    return vector_store.get_document(document_id) 