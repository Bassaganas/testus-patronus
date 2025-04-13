from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document
from typing import List, Optional, Dict, Any
import shutil
import os
import logging
from .config import settings
import time
from pathlib import Path

# Get logger
logger = logging.getLogger("testus-patronus")

class VectorStoreManager:
    def __init__(self):
        """Initialize the vector store manager with Azure OpenAI embeddings."""
        try:
            logger.info(f"Initializing embeddings with deployment: {settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT}")
            logger.info(f"Using API version: {settings.AZURE_OPENAI_API_VERSION}")
            
            # Remove trailing slash from endpoint if present
            azure_endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip('/')
            
            # Use embeddings API key
            api_key = settings.AZURE_OPENAI_EMBEDDINGS_API_KEY
            
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=azure_endpoint,
                openai_api_key=api_key,
                openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment=settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT,
                chunk_size=16  # Optimize for Azure OpenAI
            )
            
            # Create vector store directory if it doesn't exist
            self.vector_store_dir = Path(settings.VECTOR_STORE_DIR)
            self.vector_store_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize vector store with cosine similarity
            self.vector_store = Chroma(
                persist_directory=str(self.vector_store_dir),
                embedding_function=self.embeddings,
                collection_metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("Vector store manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """
        Perform a health check on the vector store.
        
        Returns:
            bool: True if the vector store is healthy, False otherwise
        """
        try:
            # Try to embed a simple test string
            test_embedding = self.embeddings.embed_query("Test health check")
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def add_documents(self, documents: List[Document], document_id: Optional[str] = None) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Document]): List of documents to add
            document_id (Optional[str]): ID of the document these chunks belong to
        """
        try:
            # Log information about the documents being added
            logger.info(f"Adding {len(documents)} documents to vector store")
            if document_id:
                logger.info(f"Document ID: {document_id}")
            
            # Add metadata if document_id is provided
            if document_id:
                for doc in documents:
                    if not doc.metadata:
                        doc.metadata = {}
                    doc.metadata["document_id"] = document_id
            
            # Add to vector store with better error handling and retries
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    self.vector_store.add_documents(documents)
                    # Note: Chroma automatically persists changes, no need to call persist()
                    logger.info(f"Successfully added documents to vector store")
                    return  # Success, exit the function
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                        raise
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def reset(self) -> None:
        """Reset the vector store by deleting all documents."""
        try:
            logger.info("Resetting vector store")
            if os.path.exists(settings.VECTOR_STORE_DIR):
                shutil.rmtree(settings.VECTOR_STORE_DIR)
                logger.info(f"Deleted vector store directory: {settings.VECTOR_STORE_DIR}")
            
            os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
            logger.info(f"Created new vector store directory: {settings.VECTOR_STORE_DIR}")
            
            # Reinitialize the vector store with better configuration
            self.vector_store = Chroma(
                persist_directory=str(self.vector_store_dir),
                embedding_function=self.embeddings,
                collection_metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store reset successful")
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None,
        score_threshold: float = 0.7
    ) -> List[Document]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            conversation_id: Limit results to a specific conversation
            project_id: Limit results to a specific project
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of Document objects
        """
        try:
            # Build filter based on conversation or project
            filter_dict: Dict[str, Any] = {}
            if conversation_id:
                filter_dict["conversation_id"] = conversation_id
                logger.info(f"Filtering search by conversation_id: {conversation_id}")
            if project_id:
                filter_dict["project_id"] = project_id
                logger.info(f"Filtering search by project_id: {project_id}")
                
            # Log the search query
            logger.info(f"Performing similarity search with query: '{query[:50]}...' (k={k})")
            
            # Perform search with filter and score threshold
            search_kwargs = {
                "k": k,
                "score_threshold": score_threshold
            }
            if filter_dict:
                search_kwargs["filter"] = filter_dict
                logger.info(f"Using filter: {filter_dict}")
            
            results = self.vector_store.similarity_search_with_score(
                query,
                **search_kwargs
            )
            
            # Convert results to Document objects with scores in metadata
            documents = []
            for doc, score in results:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata["score"] = score
                documents.append(doc)
            
            logger.info(f"Search returned {len(documents)} results")
            return documents
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    def get_document(self, document_id: str) -> List[Document]:
        """
        Retrieve all chunks for a specific document.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Retrieving document chunks for document_id: {document_id}")
            results = self.vector_store.get(
                where={"document_id": document_id},
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert results to Document objects with scores
            documents = []
            for doc, metadata, distance in zip(
                results["documents"],
                results["metadatas"],
                results["distances"]
            ):
                if not metadata:
                    metadata = {}
                metadata["score"] = 1 - distance  # Convert distance to similarity score
                documents.append(Document(page_content=doc, metadata=metadata))
            
            logger.info(f"Retrieved {len(documents)} chunks for document {document_id}")
            return documents
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: ID of the document to delete
        """
        try:
            logger.info(f"Deleting document chunks for document_id: {document_id}")
            self.vector_store.delete(
                where={"document_id": document_id}
            )
            self.vector_store.persist()  # Ensure changes are persisted
            logger.info(f"Successfully deleted chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise
    
    def delete_conversation_documents(self, conversation_id: str) -> None:
        """
        Delete all document chunks associated with a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        try:
            logger.info(f"Deleting document chunks for conversation_id: {conversation_id}")
            self.vector_store.delete(
                where={"conversation_id": conversation_id}
            )
            self.vector_store.persist()  # Ensure changes are persisted
            logger.info(f"Successfully deleted chunks for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation documents: {str(e)}")
            raise
    
    def delete_project_documents(self, project_id: str) -> None:
        """
        Delete all document chunks associated with a project.
        
        Args:
            project_id: ID of the project
        """
        try:
            logger.info(f"Deleting document chunks for project_id: {project_id}")
            self.vector_store.delete(
                where={"project_id": project_id}
            )
            self.vector_store.persist()  # Ensure changes are persisted
            logger.info(f"Successfully deleted chunks for project {project_id}")
        except Exception as e:
            logger.error(f"Error deleting project documents from vector store: {str(e)}")
            # Don't raise the error since this is not critical for project deletion
    
    def delete_collection(self) -> None:
        """
        Delete the current collection.
        """
        try:
            logger.info("Deleting entire vector store collection")
            self.vector_store.delete_collection()
            self.vector_store.persist()  # Ensure changes are persisted
            logger.info("Collection deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise 