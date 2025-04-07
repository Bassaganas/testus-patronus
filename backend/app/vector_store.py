from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import shutil
import os
from .config import settings

class VectorStoreManager:
    def __init__(self):
        """Initialize the vector store manager with Azure OpenAI embeddings."""
        try:
            print(f"Initializing embeddings with deployment: {settings.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT}")
            print(f"Using API version: {settings.AZURE_OPENAI_API_VERSION}")
            
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
            print("Vector store initialized successfully")
        except Exception as e:
            print(f"Error initializing embeddings: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[Document]): List of documents to add
        """
        # Split documents into chunks
        splits = self.text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        
        # Persist the vector store
        self.vectorstore.persist()
    
    def reset(self) -> None:
        """Reset the vector store by deleting all documents."""
        if os.path.exists(settings.VECTOR_STORE_PATH):
            shutil.rmtree(settings.VECTOR_STORE_PATH)
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        
        # Reinitialize the vector store
        self.vectorstore = Chroma(
            persist_directory=settings.VECTOR_STORE_PATH,
            embedding_function=self.embeddings
        )
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform a similarity search on the vector store.
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of Document objects
        """
        return self.vectorstore.similarity_search(query, k=k)
    
    def delete_collection(self) -> None:
        """
        Delete the current collection.
        """
        self.vectorstore.delete_collection() 