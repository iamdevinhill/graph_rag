import requests
import json
import aiohttp
from typing import List, Dict, Any, AsyncGenerator
from .config import get_settings
import logging
import hashlib
from functools import lru_cache
import asyncio

settings = get_settings()
logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_cache = {}
        self.cache_size = 1000  # Maximum number of embeddings to cache

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for the text."""
        return hashlib.md5(text.encode()).hexdigest()

    @lru_cache(maxsize=1000)
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text with caching."""
        cache_key = self._get_cache_key(text)
        
        # Check cache first
        if cache_key in self.embedding_cache:
            logger.info("Cache hit for embedding")
            return self.embedding_cache[cache_key]
        
        # Generate new embedding
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text,
                    "options": {
                        "num_thread": 4
                    }
                }
            )
            response.raise_for_status()
            embedding = response.json()["embedding"]
            
            # Update cache
            if len(self.embedding_cache) >= self.cache_size:
                # Remove oldest item if cache is full
                self.embedding_cache.pop(next(iter(self.embedding_cache)))
            self.embedding_cache[cache_key] = embedding
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def generate_response(self, prompt: str, context: str = "") -> str:
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:" if context else prompt
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.llm_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_thread": 4,
                    "num_ctx": 4096,
                    "num_batch": 512
                }
            }
        )
        response.raise_for_status()
        return response.json()["response"]

    async def generate_streaming_response(self, prompt: str, context: str = "") -> AsyncGenerator[str, None]:
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:" if context else prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "num_thread": 4,
                        "num_ctx": 4096,
                        "num_batch": 512
                    }
                }
            ) as response:
                response.raise_for_status()
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks of approximately chunk_size characters."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

ollama_service = OllamaService() 