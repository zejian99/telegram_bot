from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str
    DATABASE_KEY: str
    WEBHOOK_URL: str
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()