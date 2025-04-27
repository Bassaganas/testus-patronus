import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from langchain_core.documents import Document
from app.vector_store import VectorStoreManager

@pytest.fixture
def mock_embeddings():
    """Mock for Azure OpenAI embeddings."""
    mock = Mock()
    mock.embed_query.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding vector
    return mock

@pytest.fixture
def mock_chroma():
    """Mock for Chroma vector store."""
    mock = Mock()
    
    # Setup similarity_search_with_score mock
    mock_docs = [
        (Document(page_content="Test document 1", metadata={"document_id": "doc1", "project_id": "proj1", "conversation_id": "conv1"}), 0.1),
        (Document(page_content="Test document 2", metadata={"document_id": "doc1", "project_id": "proj1", "conversation_id": "conv1"}), 0.2),
        (Document(page_content="Test document 3", metadata={"document_id": "doc2", "project_id": "proj2", "conversation_id": "conv2"}), 0.3),
    ]
    mock.similarity_search_with_score.return_value = mock_docs
    
    # Setup get mock
    mock.get.return_value = {
        "documents": ["Test document 1", "Test document 2"],
        "metadatas": [{"document_id": "doc1"}, {"document_id": "doc1"}],
        "distances": [0.1, 0.2]
    }
    
    return mock

@pytest.fixture
def vector_store_manager(mock_embeddings, mock_chroma):
    """Create a VectorStoreManager with mocked dependencies."""
    with patch('app.vector_store.AzureOpenAIEmbeddings', return_value=mock_embeddings):
        with patch('app.vector_store.Chroma', return_value=mock_chroma):
            manager = VectorStoreManager()
            manager.embeddings = mock_embeddings
            manager.vector_store = mock_chroma
            return manager

class TestVectorStoreManager:
    def test_init(self, mock_embeddings, mock_chroma):
        """Test VectorStoreManager initialization."""
        with patch('app.vector_store.AzureOpenAIEmbeddings', return_value=mock_embeddings):
            with patch('app.vector_store.Chroma', return_value=mock_chroma):
                manager = VectorStoreManager()
                assert manager.embeddings == mock_embeddings
                assert manager.vector_store == mock_chroma

    def test_health_check_success(self, vector_store_manager, mock_embeddings):
        """Test health check when embeddings work."""
        result = vector_store_manager.health_check()
        assert result is True
        mock_embeddings.embed_query.assert_called_once()

    def test_health_check_failure(self, vector_store_manager, mock_embeddings):
        """Test health check when embeddings fail."""
        mock_embeddings.embed_query.side_effect = Exception("Test error")
        result = vector_store_manager.health_check()
        assert result is False
        mock_embeddings.embed_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_documents(self, vector_store_manager, mock_chroma):
        """Test adding documents to vector store."""
        # Create test documents
        docs = [
            Document(page_content="Test content 1"),
            Document(page_content="Test content 2")
        ]
        document_id = "test_doc_id"
        project_id = "test_project_id"
        conversation_id = "test_conv_id"
        
        # Call method
        await vector_store_manager.add_documents(docs, document_id, project_id, conversation_id)
        
        # Check that docs have been updated with metadata
        assert docs[0].metadata["document_id"] == document_id
        assert docs[0].metadata["project_id"] == project_id
        assert docs[0].metadata["conversation_id"] == conversation_id
        assert docs[1].metadata["document_id"] == document_id
        assert docs[1].metadata["project_id"] == project_id
        assert docs[1].metadata["conversation_id"] == conversation_id
        
        # Check that add_documents was called on the vector store
        mock_chroma.add_documents.assert_called_once_with(docs)

    @pytest.mark.asyncio
    async def test_add_documents_error_retry(self, vector_store_manager, mock_chroma):
        """Test retry logic when adding documents fails."""
        # Setup mock to fail once then succeed
        mock_chroma.add_documents.side_effect = [Exception("Test error"), None]
        
        # Create test documents
        docs = [Document(page_content="Test content")]
        
        # Call method
        await vector_store_manager.add_documents(docs, "test_id")
        
        # Check that add_documents was called twice (retry)
        assert mock_chroma.add_documents.call_count == 2

    def test_similarity_search_basic(self, vector_store_manager, mock_chroma):
        """Test basic similarity search."""
        # Call method
        results = vector_store_manager._execute_search("test query", 3)
        
        # Check results
        assert len(results) == 3
        mock_chroma.similarity_search_with_score.assert_called_once()
        assert "score" in results[0].metadata

    def test_similarity_search_with_filters(self, vector_store_manager, mock_chroma):
        """Test similarity search with filters."""
        # Call method with filters
        results = vector_store_manager._execute_search(
            "test query", 
            3, 
            {"project_id": "test_project"}
        )
        
        # Check that filter was passed to the search
        mock_chroma.similarity_search_with_score.assert_called_with(
            "test query", 
            k=3, 
            filter={"project_id": "test_project"}
        )

    def test_similarity_search_score_filtering(self, vector_store_manager, mock_chroma):
        """Test that results are filtered by score threshold."""
        # Setup mock to return diverse scores
        mock_chroma.similarity_search_with_score.return_value = [
            (Document(page_content="High score", metadata={}), 0.1),  # Distance of 0.1 = similarity of 0.9
            (Document(page_content="Medium score", metadata={}), 0.5),  # Distance of 0.5 = similarity of 0.5
            (Document(page_content="Low score", metadata={}), 0.8),  # Distance of 0.8 = similarity of 0.2
        ]
        
        # Call method with high threshold
        results = vector_store_manager._execute_search("test query", 3, score_threshold=0.7)
        
        # Only the high score document should pass the filter
        assert len(results) == 1
        assert results[0].page_content == "High score"
        assert results[0].metadata["score"] == 0.9

    def test_similarity_search_fallback(self, vector_store_manager, mock_chroma):
        """Test the fallback strategy when no results are found with filters."""
        # Setup mock to return empty results for first call, then results for second call
        mock_chroma.similarity_search_with_score.side_effect = [
            [],  # Empty results with combined filters
            [  # Results with just conversation_id
                (Document(page_content="Test doc", metadata={}), 0.1)  
            ]
        ]
        
        # Call method
        results = vector_store_manager.similarity_search(
            "test query", 
            conversation_id="test_conv", 
            project_id="test_proj"
        )
        
        # Check that both search attempts were made
        assert mock_chroma.similarity_search_with_score.call_count == 2
        assert len(results) == 1

    def test_get_document(self, vector_store_manager, mock_chroma):
        """Test retrieving document chunks."""
        # Call method
        results = vector_store_manager.get_document("doc1")
        
        # Check results
        assert len(results) == 2
        mock_chroma.get.assert_called_once_with(
            where={"document_id": "doc1"},
            include=["documents", "metadatas", "distances"]
        )
        assert results[0].page_content == "Test document 1"
        assert results[0].metadata["score"] == 0.9  # 1 - distance

    def test_delete_document(self, vector_store_manager, mock_chroma):
        """Test deleting document chunks."""
        # Call method
        vector_store_manager.delete_document("doc1")
        
        # Check that delete was called on the vector store
        mock_chroma.delete.assert_called_once_with(
            where={"document_id": "doc1"}
        )
        mock_chroma.persist.assert_called_once()

    def test_delete_conversation_documents(self, vector_store_manager, mock_chroma):
        """Test deleting all documents for a conversation."""
        # Call method
        vector_store_manager.delete_conversation_documents("conv1")
        
        # Check that delete was called on the vector store
        mock_chroma.delete.assert_called_once_with(
            where={"conversation_id": "conv1"}
        )
        mock_chroma.persist.assert_called_once()

    def test_delete_project_documents(self, vector_store_manager, mock_chroma):
        """Test deleting all documents for a project."""
        # Call method
        vector_store_manager.delete_project_documents("proj1")
        
        # Check that delete was called on the vector store
        mock_chroma.delete.assert_called_once_with(
            where={"project_id": "proj1"}
        )
        mock_chroma.persist.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document(self, vector_store_manager, mock_chroma):
        """Test updating document metadata."""
        # Setup mock document
        mock_document = Mock()
        mock_document.id = "doc1"
        mock_document.metadata = {"key": "value"}
        mock_document.chunks = [
            Document(page_content="chunk1", metadata={}),
            Document(page_content="chunk2", metadata={})
        ]
        
        # Mock add_documents method
        vector_store_manager.add_documents = Mock()
        
        # Call method
        await vector_store_manager.update_document(mock_document)
        
        # Check that add_documents was called with updated metadata
        call_args = vector_store_manager.add_documents.call_args[0]
        assert call_args[0] == mock_document.chunks
        assert call_args[1] == mock_document.id
        assert "key" in call_args[2].metadata
        assert call_args[2].metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_update_document_no_chunks(self, vector_store_manager, mock_chroma):
        """Test updating document with no chunks."""
        # Setup mock document with no chunks
        mock_document = Mock()
        mock_document.id = "doc1"
        mock_document.chunks = []
        
        # Mock add_documents method
        vector_store_manager.add_documents = Mock()
        
        # Call method
        await vector_store_manager.update_document(mock_document)
        
        # Check that add_documents was not called
        vector_store_manager.add_documents.assert_not_called() 