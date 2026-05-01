import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # LLM Config
    MAIN_MODEL: str = os.getenv("MAIN_AGENT_MODEL", "llama3.1:8b")
    MAIN_API_KEY: str = os.getenv("MAIN_AGENT_API_KEY", "")
    OLLAMA_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Database Config
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "Ansb6004")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "agent_marketplace")
    
    @property
    def DATABASE_URL(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        return "sqlite:///./marketplace.db"

settings = Settings()
