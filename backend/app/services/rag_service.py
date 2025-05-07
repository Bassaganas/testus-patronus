from typing import Dict, Optional, List

class RAGService:
    async def process_query(
        self,
        query: str,
        project_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        similarity_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Process a query using the RAG service.
        
        Args:
            query: The query text
            project_id: Optional project ID to scope the search
            conversation_id: Optional conversation ID for chat history
            document_ids: Optional list of document IDs to search through
            similarity_score: Optional minimum similarity score threshold (0.0 to 1.0)
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Get project documents if project_id is provided
            if project_id:
                project_docs = await self.document_repository.get_documents_by_project(project_id)
                if project_docs:
                    document_ids = [doc.id for doc in project_docs]
            
            # Process query through RAG chain
            response = await self.rag_chain.process_query(
                query=query,
                document_ids=document_ids,
                similarity_score=similarity_score
            )
            
            # Save to chat history if conversation_id provided
            if conversation_id:
                await self.chat_history_repository.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=query
                )
                await self.chat_history_repository.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response
                )
            
            return {
                "answer": response,
                "sources": []  # TODO: Add source tracking
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "answer": "I apologize, but I encountered an error while processing your question.",
                "sources": []
            } 