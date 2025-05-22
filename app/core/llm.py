import requests
from typing import List, Dict, Any
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
                "prompt": text
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
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]

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