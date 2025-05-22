# Graph RAG Application

This application implements a Retrieval Augmented Generation (RAG) system using a graph database (Neo4j) for knowledge storage and retrieval. It supports PDF document processing and provides a web interface for document ingestion and querying. The application features real-time streaming responses for an interactive chat experience.

## Prerequisites

- Docker and Docker Compose
- NVIDIA GPU with CUDA support (optional, but recommended for better performance)
- NVIDIA Container Toolkit (if using GPU)
- Or alternatively:
  - Python 3.8+
  - Neo4j Database (version 5.x)
  - Ollama (for LLM and embeddings)
  - Minimum 4GB RAM recommended for running all services
  - NVIDIA GPU with CUDA support (optional)

## GPU Support

The application supports GPU acceleration for both the API service and Ollama:

1. **Requirements**:
   - NVIDIA GPU with CUDA support
   - NVIDIA drivers installed on the host system
   - NVIDIA Container Toolkit installed

2. **Installation**:
   ```bash
   # Install NVIDIA Container Toolkit
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update
   sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

3. **Verification**:
   ```bash
   # Test NVIDIA Docker
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```

4. **CPU Fallback**:
   The application will automatically fall back to CPU if no GPU is available. To explicitly force CPU mode:
   ```bash
   # Run with CPU only
   CUDA_VISIBLE_DEVICES="" docker-compose up
   ```

   To check which mode is being used:
   ```bash
   # Check GPU usage for Ollama
   docker exec -it basic_graph-ollama-1 nvidia-smi
   
   # If no GPU is available or CPU mode is forced, you'll see an error message
   # indicating that no GPU is being used
   ```

## Setup with Docker

1. Build and start the containers:
```bash
# With GPU (if available)
docker-compose up --build

# Or force CPU mode
CUDA_VISIBLE_DEVICES="" docker-compose up --build
```

2. Pull the required Ollama models (in a new terminal):
```bash
docker exec -it basic_graph-ollama-1 ollama pull llama2
docker exec -it basic_graph-ollama-1 ollama pull nomic-embed-text
```

3. Access the application:
   - Streamlit frontend: http://localhost:8501
   - FastAPI backend: http://localhost:8000
   - Neo4j Browser: http://localhost:7474

## Manual Setup (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OLLAMA_BASE_URL=http://localhost:11434
```

3. Start Neo4j database and create a new database instance

4. Start Ollama with required models:
```bash
ollama pull llama2
ollama pull nomic-embed-text
```

5. Start the FastAPI backend:
```bash
uvicorn app.api.main:app --reload
```

6. Start the Streamlit frontend:
```bash
streamlit run app/frontend/app.py
```

## Features

- PDF document ingestion and processing
- Document embedding and vector storage
- Graph-based knowledge storage in Neo4j
- Real-time streaming responses for chat
- Semantic search capabilities
- RAG-powered question answering
- Interactive web interface
- RESTful API endpoints for programmatic access

## API Endpoints

The FastAPI backend provides the following endpoints:

- `POST /api/documents/upload`: Upload and process PDF documents
- `GET /api/documents`: List all processed documents
- `POST /api/query`: Submit questions for RAG-based answering (supports streaming)
- `GET /api/search`: Perform semantic search across documents
- `GET /api/health`: Health check endpoint

## Streaming Responses

The application implements Server-Sent Events (SSE) for real-time streaming of responses:

1. **Backend Streaming**:
   - FastAPI endpoint uses `StreamingResponse`
   - Ollama integration supports streaming generation
   - Responses are chunked and sent in real-time

2. **Frontend Streaming**:
   - Streamlit interface updates in real-time
   - Progressive display of responses
   - Context display after response completion

## Graph Schema

The application uses Neo4j to store:
- Document nodes with metadata
- Text chunks with embeddings
- Relationships between documents and chunks
- Semantic relationships between chunks

## Docker Services

The application consists of three main services:

1. **App Service**
   - FastAPI backend (port 8000)
   - Streamlit frontend (port 8501)

2. **Neo4j Database**
   - HTTP interface (port 7474)
   - Bolt protocol (port 7687)
   - Persistent data storage

3. **Ollama Service**
   - LLM and embedding service (port 11434)
   - Persistent model storage

## Troubleshooting

1. **Neo4j Connection Issues**
   - Verify Neo4j is running and accessible
   - Check credentials in .env file
   - Ensure ports 7474 and 7687 are available

2. **Ollama Model Issues**
   - Verify models are downloaded using `ollama list`
   - Check Ollama service logs for errors
   - Ensure port 11434 is accessible

3. **Document Processing Issues**
   - Check PDF file format and size
   - Verify sufficient disk space
   - Check application logs for specific errors

4. **Streaming Issues**
   - Check browser console for SSE connection errors
   - Verify network connectivity
   - Ensure no proxy or firewall is blocking SSE connections

## Development

The project structure is organized as follows:
- `app/api/`: FastAPI backend implementation
- `app/core/`: Core functionality (database, LLM, config)
- `app/frontend/`: Streamlit frontend application
- `app/models/`: Data models and schemas

## Dependencies

Key dependencies include:
- FastAPI for the backend API
- Streamlit for the frontend interface
- Neo4j for graph database
- Ollama for LLM and embeddings
- aiohttp for async HTTP requests
- sseclient-py for Server-Sent Events 