from typing import List, Dict, Any, Optional
from langchain_core.chains import RetrievalQA
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from .config import settings
from .vector_store import VectorStoreManager
from langchain_core.chains import ConversationalRetrievalChain
from langchain_core.memory import ConversationBufferMemory
from .services.database import db
from .models import Message
import logging
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Get logger
logger = logging.getLogger("testus-patronus")

class RAGChain:
    def __init__(self, vector_store: VectorStoreManager):
        """Initialize the RAG chain with the given vector store."""
        try:
            logger.info("Initializing RAG Chain")
            self.vector_store = vector_store
            
            # Initialize Azure OpenAI
            logger.info(f"Setting up Azure OpenAI with deployment: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
            self.llm = AzureChatOpenAI(
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                temperature=0.7,
                max_tokens=settings.MAX_TOKENS
            )
            
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create the prompt template
            self.prompt_template = PromptTemplate(
                template="""You are a helpful AI assistant that answers questions based on the provided context.
                Use the following pieces of context to answer the question at the end.
                If you don't know the answer, just say that you don't know, don't try to make up an answer.
                
                Context: {context}
                
                Question: {question}
                
                Answer: """,
                input_variables=["context", "question"]
            )
            
            # Initialize the QA chain
            logger.info("Initializing QA chain")
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.vectorstore.as_retriever(
                    search_kwargs={"k": 4}
                ),
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            logger.info("RAG Chain initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG Chain: {str(e)}")
            raise
    
    def get_response(self, query: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> str:
        """
        Get a response to a query, optionally in the context of a conversation or project.
        
        Args:
            query: The query to answer
            conversation_id: Optional conversation ID to provide context
            project_id: Optional project ID to provide context
            
        Returns:
            A string response to the query
        """
        try:
            logger.info(f"RAG Chain processing query: '{query[:50]}...'")
            if conversation_id:
                logger.info(f"With conversation context: {conversation_id}")
            if project_id:
                logger.info(f"With project context: {project_id}")
            
            # Get conversation history if a conversation_id is provided
            if conversation_id:
                conversation = db.get_conversation(conversation_id)
                if conversation and conversation.messages:
                    logger.info(f"Using conversation history with {len(conversation.messages)} messages")
                else:
                    logger.info("No conversation history found")
            
            # Vector store query
            try:
                # Get relevant document chunks from vector store
                docs = self.vector_store.similarity_search(
                    query, 
                    k=4, 
                    conversation_id=conversation_id,
                    project_id=project_id
                )
                
                # Log the documents we found
                if docs:
                    logger.info(f"Found {len(docs)} relevant documents")
                    for i, doc in enumerate(docs):
                        logger.debug(f"Document {i+1}: {doc.page_content[:100]}...")
                else:
                    logger.warning("No relevant documents found in vector store")
                
                # Use the QA chain to get a response
                response = self.qa_chain.run(query=query)
                # Output may be a dictionary or a string
                content = response if isinstance(response, str) else response.get("result", str(response))
                logger.info(f"Generated response: '{content[:50]}...'")
                
            except Exception as e:
                # If vector store query fails, use direct LLM interaction
                logger.error(f"Error accessing vector store: {str(e)}")
                content = "I don't have access to any documents at the moment. Please try uploading some documents first."
            
            # Ensure we're returning a string
            if not isinstance(content, str):
                content = str(content)
                
            return content
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def answer_question(self, question: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a question using the RAG chain.
        
        Args:
            question: The question to answer
            conversation_id: Optional conversation context
            project_id: Optional project context
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            # Get the relevant documents with context filtering
            relevant_docs = self.vector_store.similarity_search(
                question, 
                conversation_id=conversation_id,
                project_id=project_id
            )
            
            # Create a custom retriever that returns our pre-filtered docs
            from langchain_core.schema.retriever import BaseRetriever
            
            class ContextFilteredRetriever(BaseRetriever):
                def __init__(self, docs):
                    self.docs = docs
                    
                def get_relevant_documents(self, query):
                    return self.docs
                    
                async def aget_relevant_documents(self, query):
                    return self.docs
                    
            filtered_retriever = ContextFilteredRetriever(relevant_docs)
            
            # Create a temporary QA chain with this retriever
            temp_qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=filtered_retriever,
                chain_type_kwargs={"prompt": self.prompt_template}
            )
            
            # Get the answer
            result = temp_qa_chain({"query": question})
            
            # Get document sources
            sources = []
            doc_ids = set()
            for doc in relevant_docs:
                if "document_id" in doc.metadata:
                    doc_id = doc.metadata["document_id"]
                    if doc_id not in doc_ids:
                        doc_ids.add(doc_id)
                        doc_metadata = db.get_document(doc_id)
                        if doc_metadata:
                            sources.append({
                                "id": doc_id,
                                "filename": doc_metadata.filename,
                                "metadata": doc_metadata.metadata
                            })
            
            return {
                "answer": result["result"],
                "sources": sources
            }
        except Exception as e:
            return {
                "error": str(e),
                "answer": "I apologize, but I encountered an error while processing your question.",
                "sources": []
            } 