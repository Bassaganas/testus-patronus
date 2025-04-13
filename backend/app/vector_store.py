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
    
    def add_documents(self, documents: List[Document], document_id: Optional[str] = None, 
                    project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Document]): List of documents to add
            document_id (Optional[str]): ID of the document these chunks belong to
            project_id (Optional[str]): Project ID to associate with the document
            conversation_id (Optional[str]): Conversation ID to associate with the document
        """
        try:
            # Log information about the documents being added
            logger.info(f"Adding {len(documents)} documents to vector store")
            if document_id:
                logger.info(f"Document ID: {document_id}")
            
            # Add metadata to documents
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                if document_id:
                    doc.metadata["document_id"] = document_id
                
                # Check if project_id and conversation_id are passed directly
                if project_id:
                    doc.metadata["project_id"] = project_id
                    logger.info(f"Adding project_id to document metadata: {project_id}")
                if conversation_id:
                    doc.metadata["conversation_id"] = conversation_id
                    logger.info(f"Adding conversation_id to document metadata: {conversation_id}")
                
                # Check if metadata contains project_id or conversation_id
                if not project_id and "metadata" in doc.metadata and doc.metadata.get("metadata", {}).get("project_id"):
                    doc.metadata["project_id"] = doc.metadata["metadata"]["project_id"]
                    logger.info(f"Adding project_id from document metadata: {doc.metadata['project_id']}")
                if not conversation_id and "metadata" in doc.metadata and doc.metadata.get("metadata", {}).get("conversation_id"):
                    doc.metadata["conversation_id"] = doc.metadata["metadata"]["conversation_id"]
                    logger.info(f"Adding conversation_id from document metadata: {doc.metadata['conversation_id']}")
            
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
        score_threshold: float = 0.5  # Lowered from 0.7 to be less strict
    ) -> List[Document]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            conversation_id: Limit results to a specific conversation
            project_id: Limit results to a specific project
            score_threshold: Minimum similarity score threshold (applied post-query)
            
        Returns:
            List of Document objects
        """
        try:
            # First try with both filters if both are provided
            if conversation_id and project_id:
                filter_dict = {
                    "$and": [
                        {"conversation_id": conversation_id},
                        {"project_id": project_id}
                    ]
                }
                logger.info(f"Filtering search by conversation_id: {conversation_id} AND project_id: {project_id}")
                
                # Try the combined filter first
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                
                # If no results, try with just conversation_id
                logger.info(f"No results with combined filters, trying just conversation_id: {conversation_id}")
                filter_dict = {"conversation_id": conversation_id}
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                
                # If still no results, try with just project_id
                logger.info(f"No results with conversation_id, trying just project_id: {project_id}")
                filter_dict = {"project_id": project_id}
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                
                # If still no results, try without filters but with a lower threshold
                logger.info("No results with any filters, trying without filters")
                return self._execute_search(query, k, None, score_threshold * 0.7)  # Lower threshold by 30%
                
            elif conversation_id:
                # Only conversation_id provided
                filter_dict = {"conversation_id": conversation_id}
                logger.info(f"Filtering search by conversation_id: {conversation_id}")
                
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                    
                # Try without filters if no results
                logger.info("No results with conversation_id filter, trying without filters")
                return self._execute_search(query, k, None, score_threshold * 0.7)
                
            elif project_id:
                # Only project_id provided
                filter_dict = {"project_id": project_id}
                logger.info(f"Filtering search by project_id: {project_id}")
                
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                    
                # Try without filters if no results
                logger.info("No results with project_id filter, trying without filters")
                return self._execute_search(query, k, None, score_threshold * 0.7)
                
            else:
                # No filters provided
                logger.info("No filters provided, searching all documents")
                return self._execute_search(query, k, None, score_threshold)
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            # Return empty results instead of raising to avoid breaking the entire query
            logger.warning("Returning empty results due to search error")
            return []
            
    def _execute_search(self, query: str, k: int, filter_dict: Optional[Dict] = None, score_threshold: float = 0.5) -> List[Document]:
        """
        Helper method to execute a search with the given parameters and filter results by score.
        
        Args:
            query: The search query
            k: Number of results to return
            filter_dict: Filter dictionary for the search
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of filtered Document objects
        """
        try:
            # Log the search query
            logger.info(f"Performing similarity search with query: '{query[:50]}...' (k={k})")
            
            # Prepare search kwargs
            search_kwargs = {"k": k}
            if filter_dict:
                search_kwargs["filter"] = filter_dict
                logger.info(f"Using filter: {filter_dict}")
            
            # Execute search
            results = self.vector_store.similarity_search_with_score(query, **search_kwargs)
            
            # Apply score threshold manually after the query
            filtered_results = []
            for doc, score in results:
                # Note: similarity_search_with_score returns distance, not similarity
                # Lower distance means higher similarity, so we need to invert the comparison
                similarity = 1.0 - score  # Convert distance to similarity score
                if similarity >= score_threshold:
                    if not doc.metadata:
                        doc.metadata = {}
                    doc.metadata["score"] = similarity
                    filtered_results.append(doc)
            
            logger.info(f"Search returned {len(filtered_results)} results after filtering by score threshold {score_threshold}")
            return filtered_results
            
        except Exception as e:
            logger.warning(f"Error in execute_search: {str(e)}")
            return []
    
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
            # Don't raise, as this shouldn't block operations
            logger.warning(f"Failed to delete document chunks for {document_id}")
    
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
            # Don't raise, as this shouldn't block operations
            logger.warning(f"Failed to delete document chunks for conversation {conversation_id}")
    
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
            logger.warning(f"Failed to delete document chunks for project {project_id}")
    
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
    
    def update_document(self, document) -> None:
        """
        Update document metadata in vector store.
        
        Args:
            document: The document with updated metadata
        """
        try:
            logger.info(f"Updating document metadata in vector store for document_id: {document.id}")
            
            # First, retrieve all chunks for this document
            document_chunks = self.get_document(document.id)
            
            if not document_chunks:
                logger.warning(f"No chunks found for document {document.id} in vector store. Skipping update.")
                return
                
            # Delete existing chunks
            self.delete_document(document.id)
            
            # Extract project_id and conversation_id from document
            project_id = document.project_id
            conversation_id = document.conversation_id
            
            # Create new Langchain documents with updated metadata
            updated_chunks = []
            for chunk in document_chunks:
                # Create a new metadata dictionary with updated values
                metadata = chunk.metadata.copy() if chunk.metadata else {}
                if project_id:
                    metadata["project_id"] = project_id
                if conversation_id:
                    metadata["conversation_id"] = conversation_id
                
                # Create a new document with the updated metadata
                updated_chunk = Document(
                    page_content=chunk.page_content,
                    metadata=metadata
                )
                updated_chunks.append(updated_chunk)
            
            # Re-add the chunks with updated metadata
            self.add_documents(
                updated_chunks, 
                document_id=document.id,
                project_id=project_id,
                conversation_id=conversation_id
            )
            
            logger.info(f"Successfully updated metadata for {len(updated_chunks)} chunks in document {document.id}")
            
        except Exception as e:
            logger.error(f"Error updating document metadata in vector store: {str(e)}")
            # Don't raise, as this should not block the main update operation
            logger.warning("Document updated in database but vector store update failed") 