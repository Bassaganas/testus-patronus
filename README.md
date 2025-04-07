# Testus Patronus 🪄

A RAG-based Educational Assistant that helps students learn by leveraging document-based question answering.

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
