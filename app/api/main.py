from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import time
from collections import defaultdict
import PyPDF2
import io

from app.core.database import db
from app.core.llm import ollama_service
from app.core.init_db import initialize_database
from app.utils.gpu_utils import initialize_gpu, get_gpu_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=4)  # Adjust based on your CPU cores

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_MAX_REQUESTS = 100  # Maximum requests per window
rate_limit_store = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean up old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if rate limit exceeded
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
    
    # Add current request
    rate_limit_store[client_ip].append(current_time)
    
    # Process request
    response = await call_next(request)
    return response

class Document(BaseModel):
    content: str
    metadata: Optional[dict] = None

class Query(BaseModel):
    text: str

async def process_chunk(chunk: str, doc_id: str, chunk_index: int):
    chunk_id = f"{doc_id}_chunk_{chunk_index}"
    try:
        embedding = await asyncio.get_event_loop().run_in_executor(
            executor,
            ollama_service.generate_embedding,
            chunk
        )
        await asyncio.get_event_loop().run_in_executor(
            executor,
            db.create_chunk,
            chunk_id,
            chunk,
            embedding,
            doc_id
        )
        return True
    except Exception as e:
        logger.error(f"Error processing chunk {chunk_index}: {str(e)}", exc_info=True)
        return False

@app.post("/documents")
async def ingest_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # Read file content based on file type
        if file.content_type == "application/pdf":
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
        else:
            # For text files
            content = await file.read()
            text_content = content.decode('utf-8')
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text content could be extracted from the file")
        
        logger.info(f"Extracted {len(text_content)} characters from file")
        
        # Create document metadata
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content)
        }
        
        doc_id = str(uuid.uuid4())
        logger.info(f"Created document ID: {doc_id}")
        
        # Store document in database
        await asyncio.get_event_loop().run_in_executor(
            executor,
            db.create_document,
            doc_id,
            text_content,
            metadata
        )
        
        # Chunk the document
        chunks = ollama_service.chunk_text(text_content)
        logger.info(f"Created {len(chunks)} chunks from document")
        
        # Process chunks in parallel
        tasks = [
            process_chunk(chunk, doc_id, i)
            for i, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)
        
        if not all(results):
            raise Exception("Some chunks failed to process")
        
        logger.info("Document ingestion completed successfully")
        return {"message": "Document ingested successfully", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_documents(query: Query):
    try:
        logger.info(f"Received query: {query.text}")
        
        # Generate embedding for the query
        query_embedding = ollama_service.generate_embedding(query.text)
        logger.info("Generated query embedding")
        
        # Search for similar chunks
        similar_chunks = db.search_similar_chunks(query_embedding)
        logger.info(f"Found {len(similar_chunks) if similar_chunks else 0} similar chunks")
        
        if not similar_chunks:
            return StreamingResponse(
                iter([f"data: {json.dumps({'chunk': 'No relevant information found.'})}\n\n"]),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # Combine context from similar chunks
        context = "\n".join([chunk["content"] for chunk in similar_chunks])
        logger.info("Combined context from chunks")
        
        async def generate_stream():
            try:
                # Stream the response using Ollama's streaming capability
                async for chunk in ollama_service.generate_streaming_response(query.text, context):
                    if chunk and chunk.strip():  # Only send non-empty chunks
                        message = json.dumps({'chunk': chunk})
                        yield f"data: {message}\n\n"
                
                # Send the context at the end
                context_message = json.dumps({'context': context})
                yield f"data: {context_message}\n\n"
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                error_message = json.dumps({'chunk': 'Error generating response.'})
                yield f"data: {error_message}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return StreamingResponse(
            iter([f"data: {json.dumps({'chunk': f'Error: {str(e)}'})}\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

@app.get("/health")
async def health_check():
    try:
        # Test Neo4j connection
        with db.get_session() as session:
            session.run("RETURN 1")
        return {"status": "healthy", "neo4j": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gpu-info")
async def gpu_info():
    """Get information about GPU availability and status."""
    try:
        return get_gpu_info()
    except Exception as e:
        logger.error(f"Error getting GPU info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
async def get_graph_data():
    try:
        with db.get_session() as session:
            # Query to get all documents and their chunks
            query = """
            MATCH (d:Document)-[r:CONTAINS]->(c:Chunk)
            RETURN d, c, r
            """
            result = session.run(query)
            
            # Process the results
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                # Process document node
                doc = record["d"]
                if doc.id not in node_ids:
                    metadata = doc.get("metadata")
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except json.JSONDecodeError:
                            metadata = {}
                    
                    nodes.append({
                        "id": doc.id,
                        "label": metadata.get("filename", "Document") if metadata else "Document",
                        "type": "Document",
                        "properties": {
                            "description": doc.get("content", "")[:100] + "..."
                        }
                    })
                    node_ids.add(doc.id)
                
                # Process chunk node
                chunk = record["c"]
                if chunk.id not in node_ids:
                    nodes.append({
                        "id": chunk.id,
                        "label": "Chunk",
                        "type": "Chunk",
                        "properties": {
                            "description": chunk.get("content", "")[:100] + "..."
                        }
                    })
                    node_ids.add(chunk.id)
                
                # Process relationship
                relationships.append({
                    "startNode": doc.id,
                    "endNode": chunk.id,
                    "type": "CONTAINS"
                })
            
            return {
                "nodes": nodes,
                "relationships": relationships
            }
    except Exception as e:
        logger.error(f"Error fetching graph data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "Welcome to the Document Query API",
        "endpoints": {
            "/documents": "POST - Ingest a new document",
            "/query": "POST - Query documents",
            "/health": "GET - Check API health",
            "/gpu-info": "GET - Get GPU information",
            "/graph": "GET - Get graph data"
        }
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API service")
    # Initialize GPU settings
    initialize_gpu()
    logger.info("GPU settings initialized")
    db.create_constraints()
    initialize_database()
    logger.info("API service startup complete") 