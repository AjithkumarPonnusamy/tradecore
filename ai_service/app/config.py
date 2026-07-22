import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Self-Hosted LLM & Whisper Settings
    LLM_API_BASE: str = "http://ollama:11434/v1"
    LLM_MODEL: str = "llama3.2:1b"
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cpu"
    
    # OpenAI Settings (for Cloud fallback)
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
