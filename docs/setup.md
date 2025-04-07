# Testus Patronus - Setup Guide

This guide will help you set up and run the Testus Patronus project, a RAG (Retrieval-Augmented Generation) educational demo.

## Prerequisites

1. GitHub account (for Codespaces)
2. Azure subscription
3. Azure OpenAI API access
4. Basic understanding of Python and React

## Development Environment Setup

### Using GitHub Codespaces (Recommended)

1. Fork this repository to your GitHub account
2. Click the "Code" button and select "Create codespace on main"
3. Wait for the codespace to initialize (this may take a few minutes)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/testus-patronus.git
   cd testus-patronus
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

## Azure OpenAI Setup

1. Create an Azure OpenAI resource in your Azure portal
2. Deploy a model (e.g., gpt-35-turbo)
3. Get your API key and endpoint
4. Update the `.env` file with your credentials

## Running the Application

1. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

## Project Structure

```
testus-patronus/
├── .devcontainer/           # Dev container configuration
├── frontend/                # React frontend application
├── backend/                 # Python backend application
│   ├── app/                # Main application code
│   ├── tests/              # Test suite
│   └── data/               # Sample data and document processing
├── docs/                   # Project documentation
└── exercises/              # Student exercises and challenges
```

## Testing the RAG System

1. Prepare some sample documents (PDF, TXT, MD, or HTML)
2. Use the chat interface to ask questions about your documents
3. The system will retrieve relevant information and provide answers with sources

## Troubleshooting

### Common Issues

1. **Backend Connection Issues**
   - Check if the backend server is running
   - Verify the API endpoint in the frontend configuration
   - Check CORS settings if needed

2. **Azure OpenAI Issues**
   - Verify your API key and endpoint
   - Check if your model deployment is active
   - Ensure you have sufficient quota

3. **Vector DB Issues**
   - Check if ChromaDB is running
   - Verify the persistence directory exists and is writable

## Next Steps

1. Review the exercises in the `exercises/` directory
2. Try modifying the RAG parameters in `backend/app/config.py`
3. Experiment with different document types and chunking strategies
4. Customize the prompt template in `backend/app/rag_chain.py`

## Contributing

Please read `CONTRIBUTING.md` for details on our code of conduct and the process for submitting pull requests. 