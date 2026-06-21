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

    class Config:
        env_file = ".env"


settings = Settings()