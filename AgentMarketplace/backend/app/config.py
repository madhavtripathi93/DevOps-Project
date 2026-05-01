import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # LLM Config
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama") # 'ollama', 'openai', 'groq'
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL_OVERRIDE: str = os.getenv("LLM_MODEL_OVERRIDE", "") 
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Database Config
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "Ansb6004")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "agent_marketplace")
    
    @property
    def DATABASE_URL(self) -> str:
        # Allow full override via env
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        # Default to MySQL
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

settings = Settings()
