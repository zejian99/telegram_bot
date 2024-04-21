from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    CHAT_ID: int
    DATABASE_URL: str
    DATABASE_KEY: str
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()