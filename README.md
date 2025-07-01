# Graph RAG Application

This application implements a Retrieval Augmented Generation (RAG) system using a graph database (Neo4j) for knowledge storage and retrieval. It supports PDF and text document processing and provides a web interface for document ingestion, querying, and knowledge graph visualization. The application features real-time streaming responses for an interactive chat experience.

## Prerequisites

- Docker and Docker Compose
- Or alternatively:
  - Python 3.8+
  - Neo4j Database (version 5.17.0)
  - Ollama (for LLM and embeddings)
  - Minimum 4GB RAM recommended for running all services

## Setup with Docker

1. Build and start the containers:
```bash
docker-compose up --build
```

2. Pull the required Ollama models (in a new terminal):
```bash
docker exec -it basic_graph-ollama-1 ollama pull llama3.2
docker exec -it basic_graph-ollama-1 ollama pull nomic-embed-text
```

3. Access the application:
   - Web Interface: http://localhost
   - FastAPI backend: http://localhost:8001
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
ollama pull llama3.2
ollama pull nomic-embed-text
```

5. Start the FastAPI backend:
```bash
uvicorn app.api.main:app --reload --port 8001
```

6. Open the static web frontend:
   - Open `app/frontend/web/index.html` in your browser, or
   - Serve the `app/frontend/web/` directory using any static file server (e.g., Nginx, Python's `http.server`)

## Features

- PDF and text document ingestion and processing
- Document embedding and vector storage
- Graph-based knowledge storage in Neo4j
- Real-time streaming responses for chat
- Semantic search capabilities (via RAG)
- RAG-powered question answering
- Interactive static web interface (HTML/JS/CSS)
- RESTful API endpoints for programmatic access
- Knowledge graph visualization

## API Endpoints

The FastAPI backend provides the following endpoints:

- `POST /documents`: Upload and process PDF or text documents
- `POST /query`: Submit questions for RAG-based answering (supports streaming)
- `GET /health`: Health check endpoint
- `GET /graph`: Get graph data for visualization
- `GET /`: Root endpoint with API information

> **Note:** There are no `/api/documents`, `/api/search`, or `/api/documents/upload` endpoints. The `/api/` prefix is not used in the actual endpoints.

## Streaming Responses

The application implements Server-Sent Events (SSE) for real-time streaming of responses:

1. **Backend Streaming**:
   - FastAPI endpoint uses `StreamingResponse`
   - Ollama integration supports streaming generation
   - Responses are chunked and sent in real-time

2. **Frontend Streaming**:
   - The static web interface updates in real-time
   - Progressive display of responses
   - Context display after response completion

## Graph Schema

The application uses Neo4j to store:
- Document nodes with metadata
- Text chunks with embeddings
- Relationships between documents and chunks
- Semantic relationships between chunks

## Docker Services

The application consists of four main services:

1. **API Service**
   - FastAPI backend (port 8001)
   - CPU-optimized processing
   - Health checks and monitoring

2. **Frontend Service**
   - Nginx-based web interface (port 80)
   - Reverse proxy to API service
   - Static file serving

3. **Neo4j Database**
   - HTTP interface (port 7474)
   - Bolt protocol (port 7687)
   - Persistent data storage
   - Memory configuration optimized for 4GB RAM

4. **Ollama Service**
   - LLM and embedding service (port 11434)
   - CPU-optimized inference
   - Persistent model storage
   - Automatic model loading

## Troubleshooting

1. **Neo4j Connection Issues**
   - Verify Neo4j is running and accessible
   - Check credentials in .env file
   - Ensure ports 7474 and 7687 are available
   - Check Neo4j logs: `docker logs basic_graph-neo4j-1`

2. **Ollama Model Issues**
   - Verify models are downloaded using `ollama list`
   - Check Ollama service logs: `docker logs basic_graph-ollama-1`
   - Ensure port 11434 is accessible

3. **Document Processing Issues**
   - Check PDF or text file format and size
   - Verify sufficient disk space
   - Check application logs: `docker logs basic_graph-api-1`

4. **Streaming Issues**
   - Check browser console for SSE connection errors
   - Verify network connectivity
   - Ensure no proxy or firewall is blocking SSE connections
   - Check API logs for streaming errors

## Development

The project structure is organized as follows:
- `app/api/`: FastAPI backend implementation
- `app/core/`: Core functionality (database, LLM, config)
- `app/frontend/web/`: Static web frontend (HTML, JS, CSS)
- `app/utils/`: Utility functions and helpers (currently empty)

## Dependencies

Key dependencies include:
- FastAPI 0.109.2 for the backend API
- Neo4j 5.17.0 for graph database
- Ollama for LLM and embeddings
- PyTorch 2.2.0 (CPU version)
- aiohttp 3.9.3 for async HTTP requests
- sseclient-py 1.7.2 for Server-Sent Events

## Technical Architecture

1. **Backend (FastAPI)**
   - **Framework:**
     - Built with FastAPI for asynchronous, high-performance REST APIs.
   - **Endpoints:**
     - `POST /documents`: Handles PDF and text file uploads, extracts and chunks text, and stores both content and metadata.
     - `POST /query`: Accepts user queries, generates embeddings, performs semantic search, and streams LLM-generated responses.
     - `GET /graph`: Exposes graph data for frontend visualization.
     - `GET /health` and `GET /`: For health checks and API discovery.
   - **Streaming:**
     - Implements Server-Sent Events (SSE) for real-time, chunked response streaming to the frontend.
   - **Concurrency:**
     - Uses a thread pool executor for parallel document chunk processing.

2. **Core Services**
   - **LLM & Embeddings:**
     - Integrates with Ollama for both LLM inference and embedding generation.
     - Embeddings are used for semantic similarity search against stored document chunks.
   - **Graph Database (Neo4j):**
     - Stores documents, text chunks, and their relationships as nodes and edges.
     - Schema supports metadata, chunk embeddings, and semantic relationships.
     - Enables efficient retrieval and visualization of document knowledge graphs.

3. **Frontend (Static Web App)**
   - **Technology Stack:**
     - Pure HTML, JavaScript, and CSS (no Streamlit).
     - Served via Nginx in production.
   - **Features:**
     - Drag-and-drop document upload (PDF/TXT).
     - Real-time chat interface for querying the knowledge base.
     - Live streaming of LLM responses using SSE.
     - Interactive knowledge graph visualization (using vis.js), with controls for zoom, refresh, and node inspection.
     - Status and error feedback for robust UX.

4. **Containerization & Deployment**
   - **Dockerized Microservices:**
     - Four main containers: FastAPI backend, Nginx frontend, Neo4j, and Ollama.
     - Docker Compose manages orchestration, health checks, and environment configuration.
   - **Configuration:**
     - All service endpoints and credentials are managed via environment variables and `.env` files.

## Key Functional Flows

- **Document Ingestion:**
  - User uploads a PDF or text file via the frontend.
  - Backend extracts text, chunks it, generates embeddings, and stores all data in Neo4j.
- **Query & Retrieval:**
  - User submits a query.
  - Backend generates an embedding for the query, retrieves semantically similar chunks from Neo4j, and streams a context-aware LLM response.
- **Graph Visualization:**
  - Frontend fetches graph data and renders an interactive visualization, allowing users to explore document relationships and semantic structure.

## Design Considerations

- **Separation of Concerns:**
  - Clear modular separation between API, core logic, and frontend.
- **Scalability:**
  - Asynchronous processing and thread pools enable efficient handling of concurrent uploads and queries.
- **Extensibility:**
  - Easy to swap out LLM/embedding providers or extend the graph schema.
- **Security & Rate Limiting:**
  - Basic rate limiting middleware is implemented to prevent abuse.
