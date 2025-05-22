from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    LLM_MODEL: str = "llama2"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 