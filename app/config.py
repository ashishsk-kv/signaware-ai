from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://username:password@localhost:5432/signaware_db"
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:8b"
    
    # FastAPI Configuration
    secret_key: str = "your-secret-key-here"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LangChain Configuration
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings() 