# Testus Patronus Backend

A FastAPI-based backend for document processing and RAG (Retrieval-Augmented Generation).

## Clean Architecture

This project follows Clean Architecture principles, which separates the codebase into distinct layers:

### 1. Domain Layer

The domain layer contains the core business logic and entities of the application. It is the most inner layer and has no dependencies on other layers.

- **Domain Models**: Core business entities (e.g., `Project`, `Document`, `Conversation`)
- **Domain Schemas**: Data transfer objects (DTOs) for API requests and responses

### 2. Application Layer

The application layer contains the business logic and use cases of the application. It depends on the domain layer.

- **Services**: Business logic and use cases (e.g., `ProjectService`, `DocumentService`)
- **Repositories**: Interfaces for data access (e.g., `ProjectRepository`, `DocumentRepository`)

### 3. Infrastructure Layer

The infrastructure layer contains the implementation details of the application. It depends on the application layer.

- **Database**: Database models and session management
- **Vector Store**: Vector store implementation for document embeddings
- **External Services**: Integration with external services

### 4. API Layer

The API layer contains the entry points of the application. It depends on the application layer.

- **Endpoints**: API endpoints (e.g., `/projects`, `/documents`, `/conversations`)
- **Dependencies**: Dependency injection for services and repositories
- **Exceptions**: API-specific exceptions

## Project Structure

```
backend/
├── app/
│   ├── api/                  # API Layer
│   │   ├── v1/
│   │   │   ├── endpoints/    # API endpoints
│   │   │   ├── dependencies/ # Dependency injection
│   │   │   ├── exceptions.py # API exceptions
│   │   │   └── router.py     # API router
│   │   └── __init__.py
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Application configuration
│   │   ├── exceptions.py     # Core exceptions
│   │   └── logging.py        # Logging configuration
│   ├── domain/               # Domain Layer
│   │   ├── models/           # Domain models
│   │   └── schemas/          # Domain schemas
│   ├── infrastructure/       # Infrastructure Layer
│   │   ├── database/         # Database implementation
│   │   └── vector_store/     # Vector store implementation
│   ├── repositories/         # Repository implementations
│   ├── services/             # Service implementations
│   ├── main.py               # Application entry point
│   └── __init__.py
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables: `cp .env.example .env`
4. Run the application: `python -m app.main`

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI: `/openapi.json`

## Development

### Adding a New Feature

1. Define the domain model and schema in the domain layer
2. Implement the repository in the repositories layer
3. Implement the service in the services layer
4. Create the API endpoint in the API layer

### Testing

Run tests with pytest:

```bash
pytest
```

## License

MIT

## Quick Start with GitHub Codespaces

1. Click the green "Code" button on the repository
2. Select "Create codespace on main"
3. Wait for the environment to build (this may take a few minutes)
4. Once ready, the backend will be automatically configured with development settings

## Running the Application

### Using VS Code Debug Panel (Recommended)
1. Open the "Run and Debug" panel (Ctrl/Cmd + Shift + D)
2. Select "Python: FastAPI" from the dropdown
3. Click the green play button or press F5
4. The API will be available at:
   - Local: http://localhost:8000
   - Codespaces: Click the link in the "PORTS" tab (usually https://[codespace-name]-8000.[region].app.github.dev)

### Using Terminal
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment (if not already activated)
source /opt/venv/bin/activate

# Run the application
python run.py
```

## Environment Variables

The application comes pre-configured for development with `.env.development`. Here's what each variable means:

### Azure OpenAI Settings
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key (dummy value for development)
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: The deployment name for your model
- `AZURE_OPENAI_API_VERSION`: API version to use

### Application Settings
- `HOST`: Server host (0.0.0.0 allows external access)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (True/False)
- `ALLOWED_ORIGINS`: CORS allowed origins

### Vector DB Settings
- `VECTOR_STORE_PATH`: Path to vector store data
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB persistence directory

### Document Processing Settings
- `MAX_DOCUMENT_SIZE_MB`: Maximum document size in MB
- `CHUNK_SIZE`: Size of text chunks for processing
- `CHUNK_OVERLAP`: Overlap between chunks
- `MAX_TOKENS`: Maximum tokens for API requests

### Database Settings
- `DATABASE_URL`: SQLite database location

## Development Tools

The environment comes with:
- SQLite viewer (VS Code extension)
- Python debugging support
- Auto-formatting (black)
- Linting (flake8)
- Import sorting (isort)
- Git integration
- Database management tools

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :8000
   kill -9 <PID>
   ```

2. **Environment Variables Not Loading**
   - Check if `.env` exists in the backend directory
   - If not, it will be automatically created from `.env.development`

3. **Database Issues**
   - The SQLite database will be automatically created at first run
   - You can view it using the SQLite Viewer extension

### Getting Help

If you encounter any issues:
1. Check the console output for error messages
2. Look for similar issues in the repository's Issues section
3. Ask for help in the course forum/chat

## Testing

Run tests using the VS Code Debug panel:
1. Select "Python: Run Tests" configuration
2. Press F5 or click the green play button

Or via terminal:
```bash
pytest -v --cov=app --cov-report=term-missing
```

## Database Initialization

Before running the backend for the first time, you must initialize the database to create all required tables and schemas. Run the following command from the `backend` directory:

```sh
PYTHONPATH=. python app/infrastructure/database/init_db.py
```

This will create all necessary tables and seed the database with a default project if needed. 