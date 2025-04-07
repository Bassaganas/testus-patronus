from typing import List, Dict, Any
from langchain.chains import RetrievalQA
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from .config import settings
from .vector_store import VectorStoreManager
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class RAGChain:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        
        # Initialize Azure OpenAI
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
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.vectorstore.as_retriever(
                search_kwargs={"k": 4}
            ),
            chain_type_kwargs={"prompt": self.prompt_template}
        )
        
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.vectorstore.as_retriever(),
            memory=self.memory,
            verbose=True
        )
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using the RAG chain.
        
        Args:
            question: The question to answer
            
        Returns:
            Dictionary containing the answer and metadata
        """
        try:
            # Get the answer from the QA chain
            result = self.qa_chain({"query": question})
            
            # Get the relevant documents
            relevant_docs = self.vector_store.similarity_search(question)
            
            return {
                "answer": result["result"],
                "sources": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in relevant_docs
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "answer": "I apologize, but I encountered an error while processing your question.",
                "sources": []
            }

    def get_response(self, query: str) -> str:
        response = self.chain({"question": query})
        return response["answer"] 