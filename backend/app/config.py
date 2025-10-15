# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    db_url: str = "sqlite:///./ai-cs-bot.db"
    context_window: int = 8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
