from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.documents import Document as LangchainDocument
from typing import List, Optional, Dict, Any, Union
import shutil
import os
import logging
from app.core.config import settings
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
    
    def add_documents(self, documents: List[Union[dict, LangchainDocument]], document_id: Optional[str] = None, 
                    project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Union[dict, LangchainDocument]]): List of documents to add
            document_id (Optional[str]): ID of the document these chunks belong to
            project_id (Optional[str]): Project ID to associate with the document
            conversation_id (Optional[str]): Conversation ID to associate with the document
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            if document_id:
                logger.info(f"Document ID: {document_id}")
            fixed_documents = []
            for doc in documents:
                # Always ensure metadata is a dict and set project_id/conversation_id if available
                if isinstance(doc, dict):
                    metadata = doc.get('metadata', {})
                    if document_id:
                        metadata["document_id"] = document_id
                    if project_id is not None:
                        metadata["project_id"] = project_id
                    if conversation_id is not None:
                        metadata["conversation_id"] = conversation_id
                    doc['metadata'] = metadata
                    logger.info(f"Indexing document (dict) with metadata: {metadata}")
                    fixed_documents.append(LangchainDocument(
                        page_content=doc.get("page_content", ""),
                        metadata=metadata
                    ))
                else:
                    if not hasattr(doc, 'metadata') or doc.metadata is None:
                        doc.metadata = {}
                    if document_id:
                        doc.metadata["document_id"] = document_id
                    if project_id is not None:
                        doc.metadata["project_id"] = project_id
                    if conversation_id is not None:
                        doc.metadata["conversation_id"] = conversation_id
                    logger.info(f"Indexing document (object) with metadata: {doc.metadata}")
                    fixed_documents.append(doc)
            max_retries = 3
            retry_delay = 2  # seconds
            for attempt in range(max_retries):
                try:
                    self.vector_store.add_documents(fixed_documents)
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
        score_threshold: float = 0.0  # Lowered from 0.7 to be less strict
    ) -> List[LangchainDocument]:
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
            # Always convert IDs to strings
            conv_id_str = str(conversation_id) if conversation_id is not None else None
            proj_id_str = str(project_id) if project_id is not None else None
            
            logger.info(f"Querying with conversation_id: {conv_id_str} (type: {type(conv_id_str)})")
            logger.info(f"Querying with project_id: {proj_id_str} (type: {type(proj_id_str)})")
            
            # First, try a search with no filters at all, to see if the vector store has any documents
            try:
                logger.info("STEP 0: Trying search with no filters to check if vector store has any documents")
                no_filter_results = self._execute_search(query, k=k, filter_dict=None, score_threshold=0.0)
                if no_filter_results:
                    # Log the metadata of all documents in the vector store to debug
                    logger.info(f"Vector store has {len(no_filter_results)} documents total")
                    for i, doc in enumerate(no_filter_results[:5]):  # Show first 5 only
                        logger.info(f"Document {i} metadata: {doc.metadata}")
                else:
                    logger.warning("Vector store appears to be empty - no documents returned with no filter")
            except Exception as e:
                logger.error(f"Error in no-filter check: {str(e)}")
            
            # Now proceed with the actual filtered search
            results = []
            filter_dict = None
            
            # Skip empty string IDs
            conv_id_str = conv_id_str if conv_id_str and conv_id_str.strip() else None
            proj_id_str = proj_id_str if proj_id_str and proj_id_str.strip() else None
            
            if conv_id_str and proj_id_str:
                filter_dict = {
                    "$and": [
                        {"conversation_id": conv_id_str},
                        {"project_id": proj_id_str}
                    ]
                }
                logger.info(f"STEP 1: Filter dict used in similarity_search: {filter_dict}")
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                logger.info(f"No results with combined filters, trying just conversation_id: {conv_id_str}")
                filter_dict = {"conversation_id": conv_id_str}
                logger.info(f"STEP 2: Filter dict used in similarity_search: {filter_dict}")
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                logger.info(f"No results with conversation_id, trying just project_id: {proj_id_str}")
                filter_dict = {"project_id": proj_id_str}
                logger.info(f"STEP 3: Filter dict used in similarity_search: {filter_dict}")
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                logger.info("No results with any filters, trying without filters")
                results = self._execute_search(query, k, None, 0.0)
                logger.info(f"STEP 4: Results with no filter: {len(results)} documents")
                return results
            elif conv_id_str:
                filter_dict = {"conversation_id": conv_id_str}
                logger.info(f"Filtering search by conversation_id: {conv_id_str}")
                logger.info(f"STEP 5: Filter dict used in similarity_search: {filter_dict}")
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                logger.info("No results with conversation_id filter, trying without filters")
                results = self._execute_search(query, k, None, 0.0)
                logger.info(f"STEP 6: Results with no filter: {len(results)} documents")
                return results
            elif proj_id_str:
                filter_dict = {"project_id": proj_id_str}
                logger.info(f"Filtering search by project_id: {proj_id_str}")
                logger.info(f"STEP 7: Filter dict used in similarity_search: {filter_dict}")
                results = self._execute_search(query, k, filter_dict, score_threshold)
                if results:
                    return results
                logger.info("No results with project_id filter, trying without filters")
                results = self._execute_search(query, k, None, 0.0)
                logger.info(f"STEP 8: Results with no filter: {len(results)} documents")
                return results
            else:
                logger.info("No filters provided, searching all documents")
                results = self._execute_search(query, k, None, score_threshold)
                logger.info(f"STEP 9: Results with no filter: {len(results)} documents")
                return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            logger.warning("Returning empty results due to search error")
            return []
            
    def _execute_search(self, query: str, k: int, filter_dict: Optional[Dict] = None, score_threshold: float = 0.5) -> List[LangchainDocument]:
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
            logger.info(f"Performing similarity search with query: '{query[:50]}...' (k={k})")
            search_kwargs = {"k": k}
            if filter_dict:
                search_kwargs["filter"] = filter_dict
                logger.info(f"Using filter: {filter_dict}")
            
            try:
                results = self.vector_store.similarity_search_with_score(query, **search_kwargs)
                # Log all results before filtering
                for doc, score in results:
                    logger.info(f"Retrieved doc metadata: {getattr(doc, 'metadata', None)}, score: {score}")
                
                filtered_results = []
                for doc, score in results:
                    similarity = 1.0 - score  # Convert distance to similarity score
                    if similarity >= score_threshold:
                        if not doc.metadata:
                            doc.metadata = {}
                        doc.metadata["score"] = similarity
                        filtered_results.append(doc)
                logger.info(f"Search returned {len(filtered_results)} results after filtering by score threshold {score_threshold}")
                return filtered_results
            except Exception as e:
                logger.error(f"Error in vector store search: {str(e)}")
                # Try a simpler approach if the complex search fails
                logger.info("Attempting fallback to basic similarity search without scores")
                try:
                    basic_results = self.vector_store.similarity_search(query, **search_kwargs)
                    return basic_results
                except Exception as e2:
                    logger.error(f"Fallback search also failed: {str(e2)}")
                    return []
                
        except Exception as e:
            logger.warning(f"Error in execute_search: {str(e)}")
            return []
    
    def get_document(self, document_id: str) -> List[LangchainDocument]:
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
                documents.append(LangchainDocument(page_content=doc, metadata=metadata))
            
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
                updated_chunk = LangchainDocument(
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