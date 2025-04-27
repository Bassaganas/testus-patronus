from typing import List, Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi import Depends
from app.core.config import settings
from app.infrastructure.vector_store.vector_store import VectorStoreManager
from app.infrastructure.database.session import get_db
from app.domain.schemas.conversation import MessageBase
import logging

# Get logger
logger = logging.getLogger("testus-patronus")

def get_rag_chain(vector_store: VectorStoreManager = Depends(VectorStoreManager)) -> 'RAGChain':
    """
    Dependency function to get a RAGChain instance.
    """
    return RAGChain(vector_store)

class RAGChain:
    DEFAULT_K = 4
    DEFAULT_SCORE_THRESHOLD = 0.7

    def __init__(self, vector_store: VectorStoreManager):
        logger.info("Initializing RAG Chain")
        self.vector_store = vector_store
        self.llm = self._setup_llm()
        self.prompt_template = self._build_prompt_template()
        self.retriever = self._build_retriever()
        self.qa_chain = self._build_qa_chain(self.retriever)

    def _setup_llm(self) -> AzureChatOpenAI:
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT.rstrip('/'),
            openai_api_key=settings.AZURE_OPENAI_CHAT_API_KEY,
            openai_api_version=settings.AZURE_OPENAI_CHAT_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
            temperature=0.7,
            max_tokens=4000
        )

    def _build_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a specialized AI assistant that helps users understand their company's projects and products.
You must answer based strictly on the provided context, which may include Jira issues, technical specifications, product requirements, user stories, test cases, and other project-related documentation.
- Always prioritize clarity, accuracy, and helpfulness.
- If multiple documents seem relevant, summarize and cross-reference them if necessary.
- If you don't find enough information to answer confidently, politely say that you don't have enough information.
- Do NOT invent details or speculate beyond the given context.
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="Context: {context}\n\nQuestion: {question}")
        ])

    def _build_retriever(self) -> Any:
        return self.vector_store.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": self.DEFAULT_K,
                "score_threshold": self.DEFAULT_SCORE_THRESHOLD
            }
        )

    @staticmethod
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

    def _build_qa_chain(self, context_source: Any) -> Any:
        return (
            RunnableParallel(
                {
                    "context": context_source | RunnableLambda(self.format_docs),
                    "question": RunnablePassthrough(),
                    "chat_history": lambda _: []
                }
            )
            | self.prompt_template
            | self.llm
            | StrOutputParser()
        )

    def get_response(self, query: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> str:
        logger.info(f"RAG Chain processing query: '{query[:50]}...'")
        chat_history = self._load_chat_history(conversation_id)

        try:
            content = self.qa_chain.invoke({
                "question": query,
                "chat_history": chat_history
            })
            logger.info(f"Generated response: '{content[:50]}...'")
            return content
        except Exception as e:
            logger.error(f"Error in RAG chain: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

    def answer_question(self, question: str, conversation_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            relevant_docs = self.vector_store.similarity_search(
                question,
                k=self.DEFAULT_K,
                conversation_id=conversation_id,
                project_id=project_id
            )
            temp_chain = self._build_qa_chain(lambda _: self.format_docs(relevant_docs))
            answer = temp_chain.invoke(question)

            sources = self._extract_sources(relevant_docs)

            return {"answer": answer, "sources": sources}
        except Exception as e:
            logger.error(f"Error in answer_question: {str(e)}")
            return {"error": str(e), "answer": "I apologize, but I encountered an error while processing your question.", "sources": []}

    async def process_query(self, query: str, documents: List) -> str:
        logger.info(f"Processing query: '{query[:50]}...' with {len(documents)} documents")

        if not documents:
            return "I don't have any documents to reference. Please upload some documents to help me provide a more informed response."

        document_ids = [str(doc.id) if hasattr(doc, 'id') else doc for doc in documents]

        try:
            relevant_docs = self.vector_store.similarity_search(
                query=query,
                k=8,
                conversation_id=None,
                project_id=None,
                score_threshold=0.0
            )
            filtered_docs = [doc for doc in relevant_docs if doc.metadata and doc.metadata.get("document_id") in document_ids]
            relevant_docs = filtered_docs if filtered_docs else relevant_docs
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return "I encountered an issue searching through the documents. Please try again or rephrase your question."

        if not relevant_docs:
            return "I couldn't find any relevant information in the documents to answer your question. Could you please rephrase or ask something else about the documents?"

        try:
            context = self.format_docs(relevant_docs)
            messages = [
                SystemMessage(content="You are a specialized AI assistant that answers questions based on the provided context. If you don't know the answer, just say that you don't know."),
                HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I encountered an issue generating a response. Please try again."

    def _load_chat_history(self, conversation_id: Optional[str]) -> List:
        if not conversation_id:
            return []

        try:
            from app.db.models import Conversation
            from app.db.session import get_db
            session = next(get_db())
            conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()

            if conversation and hasattr(conversation, 'messages'):
                return [(msg.get("role", "user"), msg.get("content", "")) for msg in conversation.messages[-5:]]
            else:
                return []
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []

    def _extract_sources(self, docs: List[Document]) -> List[Dict[str, Any]]:
        sources = []
        doc_ids = set()
        for doc in docs:
            if "document_id" in doc.metadata and doc.metadata["document_id"] not in doc_ids:
                doc_ids.add(doc.metadata["document_id"])
                try:
                    from app.db.models import Document as DBDocument
                    from app.db.session import get_db
                    session = next(get_db())
                    db_doc = session.query(DBDocument).filter(DBDocument.id == doc.metadata["document_id"]).first()
                    if db_doc:
                        sources.append({
                            "id": db_doc.id,
                            "filename": db_doc.file_name,
                            "metadata": db_doc.doc_metadata,
                            "relevance_score": doc.metadata.get("score", None)
                        })
                except Exception as e:
                    logger.error(f"Error retrieving document metadata for {doc.metadata['document_id']}: {str(e)}")
        return sources
