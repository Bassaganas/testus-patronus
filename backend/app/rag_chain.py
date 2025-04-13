from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from .config import settings
from .vector_store import VectorStoreManager
from .services.database import db
from .models import Message
import logging

# Get logger
logger = logging.getLogger("testus-patronus")

class RAGChain:
    def __init__(self, vector_store: VectorStoreManager):
        """Initialize the RAG chain with the given vector store."""
        try:
            logger.info("Initializing RAG Chain")
            self.vector_store = vector_store
            
            # Initialize Azure OpenAI
            logger.info(f"Setting up Azure OpenAI with deployment: {settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}")
            logger.info(f"Using chat API version: {settings.AZURE_OPENAI_CHAT_API_VERSION}")
            
            # Remove trailing slash from endpoint if present
            azure_endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip('/')
            
            # Use chat API key
            api_key = settings.AZURE_OPENAI_CHAT_API_KEY
            
            # Use chat deployment name
            deployment_name = settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
            
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                openai_api_key=api_key,
                openai_api_version=settings.AZURE_OPENAI_CHAT_API_VERSION,
                deployment_name=deployment_name,
                temperature=0.7,
                max_tokens=4000
            )
            
            # Create the prompt template using ChatPromptTemplate with message history support
            self.prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content="You are a helpful AI assistant that answers questions based on the provided context.\nUse the following pieces of context to answer the question at the end.\nIf you don't know the answer, just say that you don't know, don't try to make up an answer."),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="Context: {context}\n\nQuestion: {question}")
            ])
            
            # Initialize the retriever with better search parameters
            logger.info("Initializing retriever")
            self.retriever = self.vector_store.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 4,
                    "score_threshold": 0.7
                }
            )
            
            # Format retrieved documents with metadata
            def format_docs(docs: List[Document]) -> str:
                formatted_docs = []
                for doc in docs:
                    content = doc.page_content
                    if doc.metadata:
                        source = doc.metadata.get("source", "Unknown source")
                        formatted_docs.append(f"Content: {content}\nSource: {source}")
                    else:
                        formatted_docs.append(content)
                return "\n\n".join(formatted_docs)
            
            # Define the RAG chain using LCEL with better error handling
            self.qa_chain = (
                RunnableParallel(
                    {
                        "context": self.retriever | RunnableLambda(format_docs),
                        "question": RunnablePassthrough(),
                        "chat_history": lambda _: []  # Default empty chat history
                    }
                )
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            logger.info("RAG Chain initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG Chain: {str(e)}")
            raise
    
    def get_response(self, query: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> str:
        """
        Get a response to a query, optionally in the context of a conversation or project.
        """
        try:
            logger.info(f"RAG Chain processing query: '{query[:50]}...'")
            
            # Get conversation history if a conversation_id is provided
            chat_history = []
            if conversation_id:
                conversation = db.get_conversation(conversation_id)
                if conversation and conversation.messages:
                    logger.info(f"Using conversation history with {len(conversation.messages)} messages")
                    chat_history = [
                        (msg.role, msg.content) 
                        for msg in conversation.messages[-5:]  # Use last 5 messages for context
                    ]
                else:
                    logger.info("No conversation history found")
            
            try:
                # Use the QA chain to get a response with chat history
                content = self.qa_chain.invoke({
                    "question": query,
                    "chat_history": chat_history
                })
                logger.info(f"Generated response: '{content[:50]}...'")
                
            except Exception as e:
                logger.error(f"Error in RAG chain: {str(e)}")
                content = "I apologize, but I encountered an error processing your request."
            
            return content
            
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"

    def answer_question(self, question: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a question using the RAG chain with document sources.
        """
        try:
            # Get the relevant documents with context filtering and better search parameters
            relevant_docs = self.vector_store.similarity_search(
                question, 
                k=4,
                conversation_id=conversation_id,
                project_id=project_id
            )
            
            # Format documents with metadata
            def format_docs(docs: List[Document]) -> str:
                formatted_docs = []
                for doc in docs:
                    content = doc.page_content
                    if doc.metadata:
                        source = doc.metadata.get("source", "Unknown source")
                        formatted_docs.append(f"Content: {content}\nSource: {source}")
                    else:
                        formatted_docs.append(content)
                return "\n\n".join(formatted_docs)
            
            # Create a temporary chain for this specific query
            temp_chain = (
                RunnableParallel(
                    {
                        "context": lambda _: format_docs(relevant_docs),
                        "question": RunnablePassthrough(),
                        "chat_history": lambda _: []
                    }
                )
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )
            
            # Get the answer
            answer = temp_chain.invoke(question)
            
            # Get document sources with better metadata handling
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
                                "metadata": doc_metadata.metadata,
                                "relevance_score": doc.metadata.get("score", None)
                            })
            
            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error in answer_question: {str(e)}")
            return {
                "error": str(e),
                "answer": "I apologize, but I encountered an error while processing your question.",
                "sources": []
            } 