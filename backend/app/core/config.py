from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App
    BACKEND_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file="../.env",  # .env lives at the project root, one level up from backend/
        extra="ignore",
    )


settings = Settings()
