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
import re
import asyncio
import uuid

# Get logger
logger = logging.getLogger("testus-patronus")

class VectorStoreManager:
    def __init__(self, vector_store_dir: Optional[str] = None):
        """Initialize the vector store manager with Azure OpenAI embeddings.
        
        Args:
            vector_store_dir: Optional custom path for the vector store. If not provided,
                            uses the path from settings.VECTOR_STORE_DIR
        """
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
                chunk_size=1000,  # Increased from 16 to 1000 for better batching
                max_retries=3,  # Add retries for reliability
                request_timeout=30  # Add timeout to prevent hanging
            )
            
            # Create vector store directory if it doesn't exist
            self.vector_store_dir = Path(vector_store_dir) if vector_store_dir else Path(settings.VECTOR_STORE_DIR)
            self.vector_store_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to initialize the persistent vector store
            try:
                logger.info(f"Initializing vector store with directory: {self.vector_store_dir}")
                # Initialize vector store with cosine similarity
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_dir),
                    embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"}
                )
                logger.info("Persistent vector store initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing persistent vector store: {str(e)}")
                logger.info("Falling back to in-memory ChromaDB")
                # Fallback to in-memory store if persistent store fails
                self.vector_store = Chroma(
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
    
    async def add_documents(self, documents: List[Union[dict, LangchainDocument]], document_id: Optional[str] = None, 
                    project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add (either dict or LangchainDocument)
            document_id: Document ID from the database (UUID)
            project_id: Optional project ID
            conversation_id: Optional conversation ID
        """
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            logger.info(f"Current vector store directory: {self.vector_store_dir}")
            
            # First check if the vector store is initialized
            if not hasattr(self, 'vector_store') or self.vector_store is None:
                logger.error("Vector store is not initialized")
                raise ValueError("Vector store is not initialized")
            
            # Convert documents to LangchainDocument format if needed
            langchain_docs = []
            for doc in documents:
                try:
                    if isinstance(doc, dict):
                        # Ensure document_id is a string
                        if 'document_id' in doc.get('metadata', {}):
                            doc['metadata']['document_id'] = str(doc['metadata']['document_id'])
                        
                        langchain_doc = LangchainDocument(
                            page_content=doc.get('page_content', ''),
                            metadata=doc.get('metadata', {})
                        )
                    else:
                        langchain_doc = doc
                    
                    # Ensure document_id is a string
                    if 'document_id' in langchain_doc.metadata:
                        langchain_doc.metadata['document_id'] = str(langchain_doc.metadata['document_id'])
                    
                    # Log document details for debugging
                    logger.info(f"Adding document with ID: {langchain_doc.metadata.get('document_id')}")
                    logger.info(f"Document content preview: {langchain_doc.page_content[:200]}...")
                    logger.info(f"Document metadata: {langchain_doc.metadata}")
                    
                    langchain_docs.append(langchain_doc)
                    
                except Exception as e:
                    logger.error(f"Error processing document: {str(e)}")
                    continue
                
            if not langchain_docs:
                logger.error("No valid documents to add to vector store")
                raise ValueError("No valid documents to add")
            
            # Add documents to vector store
            try:
                # Log state before adding documents
                try:
                    pre_count = len(self.vector_store.get()['documents'])
                    logger.info(f"Vector store has {pre_count} documents before adding new documents")
                except Exception as e:
                    logger.error(f"Error checking vector store document count before addition: {str(e)}")
                    pre_count = 0
                
                # Run the add_documents operation in a thread pool since it's CPU-bound
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.vector_store.add_documents, langchain_docs)
                
                # Explicitly persist the vector store to ensure data is saved
                try:
                    # Call persist() on the vector store itself
                    await loop.run_in_executor(None, self.vector_store.persist)
                    logger.info("Explicitly persisted vector store after adding documents")
                except Exception as e:
                    logger.error(f"Error persisting vector store: {str(e)}")
                
                logger.info(f"Successfully added {len(langchain_docs)} documents to vector store")
                
                # Verify documents were added
                for doc in langchain_docs:
                    doc_id = doc.metadata.get('document_id')
                    if doc_id:
                        try:
                            results = await loop.run_in_executor(
                                None,
                                lambda: self.vector_store.get(
                                    where={"document_id": doc_id},
                                    include=["documents", "metadatas"]
                                )
                            )
                            if not results.get('documents'):
                                logger.error(f"Document {doc_id} was not found in vector store after addition")
                            else:
                                logger.info(f"Successfully verified document {doc_id} was added with {len(results.get('documents', []))} chunks")
                        except Exception as e:
                            logger.error(f"Error verifying document {doc_id} addition: {str(e)}")
                            
            except Exception as e:
                logger.error(f"Error adding documents to vector store: {str(e)}")
                raise ValueError(f"Failed to add documents to vector store: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in add_documents: {str(e)}")
            raise
    
    def reset(self) -> None:
        """Reset the vector store by deleting all documents."""
        try:
            logger.info("Resetting vector store")
            
            # Instead of deleting the directory, we'll either:
            # 1. Delete the collection (if supported)
            # 2. Or delete the contents while preserving the directory
            
            try:
                # Try to delete just the collection first (preferred approach)
                logger.info("Attempting to delete collection")
                self.vector_store.delete_collection()
                logger.info("Successfully deleted collection")
            except Exception as e:
                logger.error(f"Error deleting collection: {str(e)}")
                
                # Fall back to removing directory contents but preserve the path
                if os.path.exists(settings.VECTOR_STORE_DIR):
                    try:
                        # Remove contents but keep directory structure
                        shutil.rmtree(settings.VECTOR_STORE_DIR)
                        logger.info(f"Deleted vector store directory contents: {settings.VECTOR_STORE_DIR}")
                        # Recreate the same directory
                        os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
                    except Exception as e:
                        logger.error(f"Error resetting vector store directory: {str(e)}")
            
            # Maintain the same vector store directory path (don't create timestamped dirs)
            self.vector_store_dir = Path(settings.VECTOR_STORE_DIR)
            
            # Reinitialize the vector store with the same directory
            try:
                # Initialize vector store with cosine similarity
                self.vector_store = Chroma(
                    persist_directory=str(self.vector_store_dir),
                    embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"}
                )
                
                # Explicitly persist to ensure the collection is saved
                try:
                    self.vector_store.persist()
                    logger.info("Explicitly persisted vector store after reset")
                except Exception as e:
                    logger.error(f"Error persisting vector store after reset: {str(e)}")
                
                logger.info("Vector store reset successful")
            except Exception as e:
                logger.error(f"Error reinitializing vector store: {str(e)}")
                # Create an in-memory store as fallback
                logger.info("Falling back to in-memory ChromaDB")
                self.vector_store = Chroma(
                    embedding_function=self.embeddings,
                    collection_metadata={"hnsw:space": "cosine"}
                )
        except Exception as e:
            logger.error(f"Error resetting vector store: {str(e)}")
            raise
    
    def search_by_jira_key(self, jira_key: str) -> List[LangchainDocument]:
        """
        Search for documents by Jira issue key.
        
        Args:
            jira_key: The Jira issue key (e.g., 'PROJ-123')
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Searching for Jira issue with key: {jira_key}")
            
            # First try exact match in metadata
            results = self.vector_store.get(
                where={"issue_key": jira_key},
                include=["documents", "metadatas"]
            )
            
            if results and results.get("documents"):
                # Convert results to Document objects
                documents = []
                for doc, metadata in zip(
                    results["documents"],
                    results["metadatas"]
                ):
                    if not metadata:
                        metadata = {}
                    documents.append(LangchainDocument(page_content=doc, metadata=metadata))
                return documents
            
            # If no exact match, try semantic search with the key
            return self.similarity_search(
                query=f"Find the Jira issue with key {jira_key}",
                k=1,
                score_threshold=0.7
            )
            
        except Exception as e:
            logger.error(f"Error searching by Jira key: {str(e)}")
            return []

    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        conversation_id: Optional[str] = None,
        project_id: Optional[str] = None,
        score_threshold: float = 0.0,  # Lowered from 0.7 to be less strict
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[LangchainDocument]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            conversation_id: Limit results to a specific conversation
            project_id: Limit results to a specific project
            score_threshold: Minimum similarity score threshold (applied post-query)
            metadata_filters: Additional metadata filters to apply
            
        Returns:
            List of Document objects
        """
        try:
            # Always convert IDs to strings
            conv_id_str = str(conversation_id) if conversation_id is not None else None
            proj_id_str = str(project_id) if project_id is not None else None
            
            logger.info(f"Querying with conversation_id: {conv_id_str} (type: {type(conv_id_str)})")
            logger.info(f"Querying with project_id: {proj_id_str} (type: {type(proj_id_str)})")
            
            # Check if query contains a Jira key pattern (e.g., PROJ-123)
            jira_key_match = re.search(r'[A-Z]+-\d+', query)
            if jira_key_match:
                jira_key = jira_key_match.group()
                logger.info(f"Detected Jira key in query: {jira_key}")
                # Try to find the specific issue first
                key_results = self.search_by_jira_key(jira_key)
                if key_results:
                    return key_results
            
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
            
            # Build filter dictionary
            filter_conditions = []
            
            if conv_id_str:
                filter_conditions.append({"conversation_id": conv_id_str})
            if proj_id_str:
                filter_conditions.append({"project_id": proj_id_str})
            if metadata_filters:
                filter_conditions.append(metadata_filters)
            
            if filter_conditions:
                if len(filter_conditions) == 1:
                    filter_dict = filter_conditions[0]
                else:
                    filter_dict = {"$and": filter_conditions}
            
            logger.info(f"Using filter dict: {filter_dict}")
            results = self._execute_search(query, k, filter_dict, score_threshold)
            
            if not results and filter_dict:
                # If no results with filters, try without them
                logger.info("No results with filters, trying without filters")
                results = self._execute_search(query, k, None, 0.0)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
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
            document_id: UUID of the document to retrieve
            
        Returns:
            List of Document objects
        """
        try:
            logger.info(f"Retrieving document chunks for document_id: {document_id}")
            
            # First check if the vector store is initialized
            if not hasattr(self, 'vector_store') or self.vector_store is None:
                logger.error("Vector store is not initialized")
                raise ValueError("Vector store is not initialized")
            
            # Ensure document_id is a string
            document_id = str(document_id)
            logger.info(f"Using document_id (type: {type(document_id)}): {document_id}")
            
            # First try to get all documents to verify the vector store has data
            try:
                all_docs = self.vector_store.get()
                logger.info(f"Vector store contains {len(all_docs.get('documents', []))} total documents")
            except Exception as e:
                logger.error(f"Error checking vector store contents: {str(e)}")
                raise ValueError(f"Vector store may be empty or corrupted: {str(e)}")
            
            # Get the document by UUID or project_id
            try:
                # Try to get by project_id first
                results = self.vector_store.get(
                    where={"project_id": document_id},
                    include=["documents", "metadatas"]
                )
                
                # If no results, try by document_id
                if not results.get('documents'):
                    results = self.vector_store.get(
                        where={"document_id": document_id},
                        include=["documents", "metadatas"]
                    )
            except Exception as e:
                logger.error(f"Error retrieving document from vector store: {str(e)}")
                raise ValueError(f"Failed to retrieve document from vector store: {str(e)}")
            
            # Log the raw results for debugging
            logger.info(f"Raw results from vector store: {len(results.get('documents', []))} documents found")
            
            # Convert results to Document objects
            documents = []
            for i, (doc, metadata) in enumerate(zip(
                results["documents"],
                results["metadatas"]
            )):
                if not metadata:
                    metadata = {}
                documents.append(LangchainDocument(page_content=doc, metadata=metadata))
                
                # Log detailed information about each document chunk
                logger.info(f"Document chunk {i+1}/{len(results['documents'])} metadata: {metadata}")
                
                # Log a preview of the content (first 200 chars)
                content_preview = doc[:200] + "..." if len(doc) > 200 else doc
                logger.info(f"Document chunk {i+1}/{len(results['documents'])} content preview: {content_preview}")
                
                # For Jira documents, log specific fields if available
                if metadata.get("source_type") == "jira":
                    logger.info(f"Jira document chunk {i+1}/{len(results['documents'])} - Key: {metadata.get('issue_key')}, "
                               f"Type: {metadata.get('issue_type')}, Status: {metadata.get('status')}")
            
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
            logger.info("Collection deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
    
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        """
        Update metadata for a document in the vector store.
        
        Args:
            document_id: Document ID to update
            metadata: New metadata to set
        """
        try:
            # Get existing document
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.vector_store.get(
                    where={"document_id": document_id},
                    include=["documents", "metadatas"]
                )
            )
            
            if not results.get('documents'):
                raise ValueError(f"Document {document_id} not found in vector store")
            
            # Update metadata for each chunk
            updated_chunks = []
            for doc, meta in zip(results['documents'], results['metadatas']):
                updated_meta = meta.copy()
                updated_meta.update(metadata)
                updated_chunks.append(LangchainDocument(
                    page_content=doc,
                    metadata=updated_meta
                ))
            
            # Re-add the chunks with updated metadata
            await self.add_documents(
                updated_chunks, 
                document_id=document_id,
                project_id=metadata.get('project_id'),
                conversation_id=metadata.get('conversation_id')
            )
            
        except Exception as e:
            logger.error(f"Error updating document metadata: {str(e)}")
            raise

    async def update_document(self, document) -> None:
        """
        Update a document in the vector store.
        
        Args:
            document: Document to update
        """
        try:
            # Get existing document
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.vector_store.get(
                    where={"document_id": str(document.id)},
                    include=["documents", "metadatas"]
                )
            )
            
            if not results.get('documents'):
                raise ValueError(f"Document {document.id} not found in vector store")
            
            # Update metadata for each chunk
            updated_chunks = []
            for doc, meta in zip(results['documents'], results['metadatas']):
                updated_meta = meta.copy()
                updated_meta.update({
                    "project_id": str(document.project_id) if document.project_id else None,
                    "conversation_id": str(document.conversation_id) if document.conversation_id else None
                })
                updated_chunks.append(LangchainDocument(
                    page_content=doc,
                    metadata=updated_meta
                ))
            
            # Re-add the chunks with updated metadata
            await self.add_documents(
                updated_chunks, 
                document_id=str(document.id),
                project_id=str(document.project_id) if document.project_id else None,
                conversation_id=str(document.conversation_id) if document.conversation_id else None
            )
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise 