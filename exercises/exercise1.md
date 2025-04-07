# Exercise 1: Understanding RAG Implementation

## Objective
In this exercise, you will learn about the core components of a RAG system by implementing and modifying different parts of the Testus Patronus application.

## Tasks

### Task 1: Document Processing
1. Open `backend/app/document_processor.py`
2. Find the `process_document` method
3. Add support for a new document type (e.g., CSV files)
4. Implement the necessary loader and update the `loader_map`

### Task 2: Chunking Strategy
1. Open `backend/app/config.py`
2. Experiment with different chunk sizes and overlap values
3. Test how these changes affect the quality of answers
4. Document your findings in a markdown file

### Task 3: Vector Store
1. Open `backend/app/vector_store.py`
2. Modify the similarity search to use a different distance metric
3. Compare the results with the original implementation
4. Add a method to visualize the vector embeddings

### Task 4: Prompt Engineering
1. Open `backend/app/rag_chain.py`
2. Modify the prompt template to include:
   - Instructions about answer format
   - Requirements for source citations
   - Guidelines for handling uncertainty
3. Test the modified prompt with various questions

### Task 5: Frontend Enhancement
1. Open `frontend/src/components/Chat.tsx`
2. Add a feature to:
   - Display confidence scores for answers
   - Show alternative answers
   - Allow users to provide feedback on answer quality

## Hints

### Task 1 Hint
```python
# Example of adding CSV support
from langchain.document_loaders import CSVLoader

# Add to loader_map
self.loader_map["csv"] = CSVLoader
```

### Task 2 Hint
```python
# Try these configurations
CHUNK_SIZE = 500  # Smaller chunks
CHUNK_OVERLAP = 100  # Less overlap
```

### Task 3 Hint
```python
# Example of using cosine similarity
self.collection = self.client.create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)
```

### Task 4 Hint
```python
# Example prompt modification
template = """You are a helpful AI assistant that answers questions based on the provided context.
Please follow these guidelines:
1. Start with a direct answer
2. Provide supporting evidence from the context
3. If uncertain, explain your reasoning
4. Cite sources using [Source X] format

Context: {context}
Question: {question}
Answer: """
```

### Task 5 Hint
```typescript
// Example of adding confidence score
interface Message {
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: Array<{
    content: string;
    metadata: any;
  }>;
}
```

## Evaluation Criteria

1. **Code Quality**
   - Clean, well-documented code
   - Proper error handling
   - Type hints and comments

2. **Functionality**
   - All tasks completed successfully
   - New features work as expected
   - No regression in existing functionality

3. **Understanding**
   - Clear explanation of changes made
   - Understanding of RAG concepts
   - Ability to justify design decisions

## Submission

1. Create a new branch for your work
2. Commit your changes with clear messages
3. Create a pull request with:
   - Description of changes
   - Testing results
   - Any challenges encountered
   - Questions or areas for improvement

## Bonus Challenges

1. Implement a custom document loader for a specific format
2. Add support for multilingual document processing
3. Create a visualization of the RAG pipeline
4. Implement a feedback loop to improve answer quality

## Resources

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/)
- [React TypeScript Documentation](https://react-typescript-cheatsheet.netlify.app/) 