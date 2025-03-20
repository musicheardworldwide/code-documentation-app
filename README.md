# Code Documentation Application

This application analyzes GitHub repositories or zip files containing codebases and generates comprehensive documentation using LLM technology. It includes a RAG system for context-aware code understanding and can generate Q&A pairs for development and feature changes.

## Features

- Process code from GitHub repositories or zip files
- Analyze code structure and dependencies
- Generate comprehensive documentation with LLM assistance
- Create 50 Q&A items about codebase development and feature changes
- Provide context-aware code understanding through RAG
- Expose functionality through a REST API
- Support configuration through environment variables
- Easy deployment with Docker

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```
   git clone <repository-url>
   cd code-documentation-app
   ```

2. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file to configure your LLM API settings and other options.

4. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

### Manual Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd code-documentation-app
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file to configure your LLM API settings and other options.

## Usage

### API Endpoints

The application exposes the following API endpoints:

#### Health Check
- `GET /`: Check if the API is running

#### Documentation Generation
- `POST /api/github`: Process GitHub repository
  ```json
  {
    "repo_url": "https://github.com/username/repo",
    "output_dir": "optional/output/path",
    "llm_config": {
      "base_url": "https://api.example.com",
      "api_key": "your_api_key",
      "instruct_model": "model_name",
      "reasoning_model": "model_name",
      "embeddings_model": "model_name"
    }
  }
  ```

- `POST /api/zip`: Process zip file
  ```json
  {
    "file_path": "/path/to/codebase.zip",
    "output_dir": "optional/output/path",
    "llm_config": {
      "base_url": "https://api.example.com",
      "api_key": "your_api_key",
      "instruct_model": "model_name",
      "reasoning_model": "model_name",
      "embeddings_model": "model_name"
    }
  }
  ```

#### Task Management
- `GET /api/tasks/{task_id}`: Get task status

#### RAG Queries
- `POST /api/query`: Query documentation using RAG
  ```json
  {
    "query": "How does the authentication system work?",
    "task_id": "task_id_from_documentation_generation",
    "max_results": 5
  }
  ```

#### Q&A Retrieval
- `GET /api/qa/{task_id}`: Get Q&A pairs for a task

### Environment Variables

The application can be configured using the following environment variables:

#### LLM API Configuration
- `LLM_BASE_URL`: Base URL for LLM API
- `LLM_API_KEY`: API key for LLM service
- `LLM_INSTRUCT_MODEL`: Model name for instruction following
- `LLM_REASONING_MODEL`: Model name for reasoning tasks
- `LLM_EMBEDDINGS_MODEL`: Model name for embeddings generation

#### Application Configuration
- `OUTPUT_DIR`: Output directory for documentation
- `TEMP_DIR`: Temporary directory for processing
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

#### API Configuration
- `API_HOST`: Host to bind the API server
- `API_PORT`: Port to bind the API server
- `API_WORKERS`: Number of worker processes
- `API_DEBUG`: Enable debug mode
- `API_CORS_ORIGINS`: Allowed CORS origins
- `API_RATE_LIMIT`: Rate limit for API requests

#### Database Configuration
- `VECTOR_DB_PATH`: Path to vector database for RAG

## Docker Deployment

The application includes Docker configuration for easy deployment:

- `Dockerfile`: Defines the container image
- `docker-compose.yml`: Configures the service with appropriate settings

The Docker setup includes:
- Volume mounting for data persistence
- Environment variable configuration through `.env` file
- Health checks for monitoring
- Automatic restart policy

## Architecture

The application is organized into the following modules:

- `ingestion`: Handles GitHub repository cloning and zip file extraction
- `analysis`: Analyzes code structure and dependencies
- `llm_integration`: Integrates with LLM API for code understanding
- `documentation`: Generates comprehensive documentation
- `rag`: Implements Retrieval-Augmented Generation for context-aware understanding
- `ui`: Provides command-line interface
- `api`: Exposes functionality through REST API

## Using as a Tool or Knowledge/RAG API

This application can be used as:

1. **Documentation Tool**: Generate comprehensive documentation for any codebase
2. **Knowledge API**: Query the documentation to understand code structure and functionality
3. **RAG API**: Use the context-aware system to get answers about specific code aspects
4. **Development Q&A**: Access the 50 generated Q&A pairs about development and feature changes

## License

[MIT License](LICENSE)
