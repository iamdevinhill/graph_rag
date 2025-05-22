import requests
import json
import aiohttp
from typing import List, Dict, Any, AsyncGenerator
from .config import get_settings

settings = get_settings()

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    def generate_embedding(self, text: str) -> List[float]:
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.embedding_model,
                "prompt": text,
                "options": {
                    "num_gpu": 1,
                    "num_thread": 4
                }
            }
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def generate_response(self, prompt: str, context: str = "") -> str:
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:" if context else prompt
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.llm_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_gpu": 1,
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
                        "num_gpu": 1,
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
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

ollama_service = OllamaService() 