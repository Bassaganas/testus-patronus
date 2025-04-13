# Testus Patronus - RAG Document Query Application

A document query application that allows you to upload documents, create projects and conversations, and ask questions about the documents.

## Local Development Setup

### Prerequisites
- Python 3.9+ 
- Node.js 16+
- npm or yarn

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create data directories:
   ```bash
   mkdir -p data/vector_store data/db
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend development server:
   ```bash
   npm start
   ```

   If port 3000 is already in use, it will prompt you to use another port (like 3001).

## Using the Application

1. Access the application in your browser at http://localhost:3000 (or the alternative port)

2. Create a new project by clicking the + button in the sidebar

3. Create a new conversation within a project, or as a standalone conversation

4. Upload documents to projects or conversations

5. Ask questions about the uploaded documents

## Features

- **Projects**: Create projects to organize your conversations and documents
- **Conversations**: Create conversations within projects or as standalone
- **Document Management**: Upload and view documents per project or conversation
- **Document Query**: Ask questions about the uploaded documents using RAG technology

## Troubleshooting

- If you get an error about a read-only file system, make sure the VECTOR_STORE_PATH in your .env file is set to "./data/vector_store" (relative path)
- If the frontend can't connect to the backend, check that REACT_APP_API_URL in frontend/.env is set to "http://localhost:8000"
- Make sure data directories exist and have proper permissions

## 🌟 Features

- Document upload and processing (PDF, TXT, MD, HTML)
- Real-time chat interface
- RAG (Retrieval-Augmented Generation) based responses
- Azure OpenAI integration
- Vector store for efficient document retrieval
- Modern React frontend with TypeScript
- FastAPI backend with async support

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- Azure OpenAI API access
- pip and npm package managers

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/testus-patronus.git
   cd testus-patronus
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

   Create a `.env` file in the backend directory:
   ```env
   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo-16k
   AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002
   AZURE_OPENAI_API_VERSION=2023-05-15

   # Vector Store Configuration
   VECTOR_STORE_PATH=./data/vector_store

   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   DEBUG=true

   # CORS Configuration
   ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

   Create a `.env` file in the frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

## 🏃‍♂️ Running the Application

1. **Start the Backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```
   The backend will be available at http://localhost:8000

2. **Start the Frontend**
   ```bash
   cd frontend
   npm start
   ```
   The frontend will be available at http://localhost:3000

## 📚 Usage

1. **Upload Documents**
   - Click the "Choose File" button
   - Select a supported document (PDF, TXT, MD, HTML)
   - Maximum file size: 10MB
   - Wait for the upload confirmation

2. **Ask Questions**
   - Type your question in the chat input
   - Press Enter or click Send
   - The system will retrieve relevant information from your documents
   - Receive AI-generated responses based on the document content

## 🛠 Technical Stack

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- Axios for API requests
- React hooks for state management

### Backend
- FastAPI for the web framework
- LangChain for RAG implementation
- Azure OpenAI for embeddings and completions
- ChromaDB for vector storage
- Python-multipart for file uploads

## 🔒 Security Notes

- Environment variables are used for sensitive information
- CORS is configured for security
- File size and type validations are implemented
- API key handling is done securely

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Azure OpenAI for providing the AI capabilities
- LangChain for the RAG framework
- FastAPI for the efficient backend framework
- React team for the frontend framework 
