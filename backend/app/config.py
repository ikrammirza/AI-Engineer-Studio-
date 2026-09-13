from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:7b"
    database_url: str
    class Config:
        env_file = "backend/.env"


settings = Settings()