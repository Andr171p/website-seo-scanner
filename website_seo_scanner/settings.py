from typing import Final

from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


class EmbeddingsSettings(BaseSettings):
    base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_prefix="EMBEDDINGS_")


class Settings(BaseSettings):
    embeddings: EmbeddingsSettings = EmbeddingsSettings()


settings: Final[Settings] = Settings()
