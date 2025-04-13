from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Optional
import shutil
import os
import logging
from .config import settings

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
            
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=azure_endpoint,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment=settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
            )
            
            # Create vector store directory if it doesn't exist
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
            
            # Initialize the vector store
            self.vectorstore = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                embedding_function=self.embeddings
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
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
            
            # Split documents into chunks
            splits = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(splits)} chunks")
            
            # Add document_id to metadata if provided
            if document_id:
                for split in splits:
                    if not isinstance(split.metadata, dict):
                        split.metadata = {}
                    split.metadata["document_id"] = document_id
            
            # Add to vector store
            self.vectorstore.add_documents(splits)
            
            # Persist the vector store
            self.vectorstore.persist()
            logger.info(f"Successfully added documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def reset(self) -> None:
        """Reset the vector store by deleting all documents."""
        try:
            logger.info("Resetting vector store")
            if os.path.exists(settings.VECTOR_STORE_PATH):
                shutil.rmtree(settings.VECTOR_STORE_PATH)
                logger.info(f"Deleted vector store directory: {settings.VECTOR_STORE_PATH}")
            
            os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
            logger.info(f"Created new vector store directory: {settings.VECTOR_STORE_PATH}")
            
            # Reinitialize the vector store
            self.vectorstore = Chroma(
                persist_directory=settings.VECTOR_STORE_PATH,
                embedding_function=self.embeddings
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
        project_id: Optional[str] = None
    ) -> List[Document]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            conversation_id: Limit results to a specific conversation
            project_id: Limit results to a specific project
            
        Returns:
            List of Document objects
        """
        try:
            # Build filter based on conversation or project
            filter_dict = {}
            if conversation_id:
                filter_dict["conversation_id"] = conversation_id
                logger.info(f"Filtering search by conversation_id: {conversation_id}")
            if project_id:
                filter_dict["project_id"] = project_id
                logger.info(f"Filtering search by project_id: {project_id}")
                
            # Log the search query
            logger.info(f"Performing similarity search with query: '{query[:50]}...' (k={k})")
            
            # Perform search with filter if needed
            if filter_dict:
                logger.info(f"Using filter: {filter_dict}")
                results = self.vectorstore.similarity_search(
                    query, 
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)
            
            logger.info(f"Search returned {len(results)} results")
            return results
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
            results = self.vectorstore.get(
                where={"document_id": document_id}
            )
            logger.info(f"Retrieved {len(results)} chunks for document {document_id}")
            return results
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
            self.vectorstore.delete(
                where={"document_id": document_id}
            )
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
            self.vectorstore.delete(
                where={"conversation_id": conversation_id}
            )
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
            self.vectorstore.delete(
                where={"project_id": project_id}
            )
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
            self.vectorstore.delete_collection()
            logger.info("Collection deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise 