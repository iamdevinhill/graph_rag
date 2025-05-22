from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging
import json
import asyncio

from app.core.database import db
from app.core.llm import ollama_service
from app.core.init_db import initialize_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class Document(BaseModel):
    content: str
    metadata: Optional[dict] = None

class Query(BaseModel):
    text: str

@app.post("/documents")
async def ingest_document(document: Document):
    try:
        logger.info("Received document for ingestion")
        logger.info(f"Document content length: {len(document.content)} characters")
        logger.info(f"First 100 characters of content: {document.content[:100]}")
        doc_id = str(uuid.uuid4())
        logger.info(f"Created document ID: {doc_id}")
        
        logger.info("Storing document in database...")
        db.create_document(doc_id, document.content, document.metadata)
        logger.info("Document stored in database")
        
        # Chunk the document and create embeddings
        logger.info("Chunking document...")
        chunks = ollama_service.chunk_text(document.content)
        logger.info(f"Created {len(chunks)} chunks from document")
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            try:
                logger.info("Generating embedding...")
                embedding = ollama_service.generate_embedding(chunk)
                logger.info(f"Generated embedding with {len(embedding)} dimensions")
                logger.info("Storing chunk in database...")
                db.create_chunk(chunk_id, chunk, embedding, doc_id)
                logger.info(f"Stored chunk {i+1} with embedding")
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}", exc_info=True)
                raise
        
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
            return {"response": "No relevant information found."}
        
        # Combine context from similar chunks
        context = "\n".join([chunk["content"] for chunk in similar_chunks])
        logger.info("Combined context from chunks")
        
        async def generate_stream():
            # Stream the response using Ollama's streaming capability
            async for chunk in ollama_service.generate_streaming_response(query.text, context):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # Send the context at the end
            yield f"data: {json.dumps({'context': context})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up API service")
    db.create_constraints()
    initialize_database()
    logger.info("API service startup complete") 