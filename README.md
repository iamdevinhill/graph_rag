# Graph RAG Application

This application implements a Retrieval Augmented Generation (RAG) system using a graph database (Neo4j) for knowledge storage and retrieval.

## Prerequisites

- Docker and Docker Compose
- Or alternatively:
  - Python 3.8+
  - Neo4j Database
  - Ollama (for LLM and embeddings)

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

3. Start Neo4j database

4. Start Ollama with required models:
```bash
ollama pull llama3.2
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

- Document ingestion and embedding
- Graph-based knowledge storage
- Semantic search
- RAG-powered question answering
- Interactive web interface

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