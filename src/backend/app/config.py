from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Athena"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"

    DEV_MODE: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./athena_dev.db"
    DATABASE_URL_PROD: str = "postgresql+asyncpg://athena:athena@localhost:5432/athena"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "athena"
    MINIO_SECRET_KEY: str = "athena_secret"
    MINIO_BUCKET: str = "athena"

    LITELLM_API_KEY: str = ""
    LITELLM_BASE_URL: str = "http://localhost:4000"

    JWT_SECRET_KEY: str = "athena-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    MARKET_PROVIDER: str = "mock"
    REALTIME_ENABLED: bool = False
    BOOTSTRAP_ON_STARTUP: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
