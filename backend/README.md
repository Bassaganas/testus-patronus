# Testus Patronus Backend

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

## API Documentation

Once the application is running, you can access:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI Schema: `/openapi.json`

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