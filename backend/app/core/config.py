from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ServiceFlow"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    SECRET_KEY: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str
    
    SECRET_KEY: str  # gerar com: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = Settings()