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
    
    async def search_by_jira_key(self, jira_key: str) -> List[LangchainDocument]:
        try:
            logger.info(f"Searching for Jira issue with key: {jira_key}")
            
            results = self.vector_store.get(
                where={"issue_key": jira_key},
                include=["documents", "metadatas"]
            )

            if results and results.get("documents"):
                documents = [
                    LangchainDocument(page_content=doc, metadata=metadata or {})
                    for doc, metadata in zip(results["documents"], results["metadatas"])
                ]
                return documents

            return await self.similarity_search(
                query=f"Find the Jira issue with key {jira_key}",
                k=1,
                score_threshold=0.7
            )

        except Exception as e:
            logger.error(f"Error searching by Jira key: {str(e)}")
            return []


    async def similarity_search(
        self,
        query: str,
        project_id: str,
        score_threshold: Optional[float] = None,
        k: int = 10  # Default to RAGChain.DEFAULT_K
    ) -> List[LangchainDocument]:
        """
        Perform a similarity search in the vector store.
        
        Args:
            query: The query text
            document_ids: Optional list of document IDs or Document objects to search through
            score_threshold: Optional minimum similarity score threshold (0.0 to 1.0)
            k: Number of documents to retrieve (default: 4)
            
        Returns:
            List[Document]: List of relevant documents
        """
        try:
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.vector_store.similarity_search_with_score(
                    query,  # ❗ RAW TEXT
                    k=k,
                    filter={"project_id": project_id}
                )
            )

            if not results:
                logger.warning(f"No documents found in similarity search for query: {query}")
                return []

            if score_threshold is not None:
                original_len = len(results)
                results = [(doc, score) for doc, score in results if score >= score_threshold]
                if not results:
                    logger.info(f"Filtered out {original_len} results below score threshold {score_threshold}")
                    return []

            logger.info(f"Returning {len(results)} documents above threshold for query: {query}")
            return [doc for doc, _ in results]

        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
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