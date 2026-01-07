import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DB_USER: str = os.getenv('DB_USER')
    DB_NAME: str = os.getenv('DB_NAME')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: str = os.getenv('DB_PORT')

    database_url: str = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ALGORITHM: str = os.getenv('ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')

    DEBUG: bool = os.getenv('DEBUG')

    REDIS_URL: str = os.getenv('REDIS_URL', "redis://localhost:6379/0")

    EMAIL_HOST: str = os.getenv('EMAIL_HOST')
    EMAIL_PORT: int = os.getenv('EMAIL_PORT')
    EMAIL_USE_TLS: bool = os.getenv('EMAIL_USE_TLS')
    EMAIL_USE_SSL: bool = os.getenv('EMAIL_USE_SSL')
    EMAIL_HOST_USER: str = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD: str = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL: str = os.getenv('DEFAULT_FROM_EMAIL')

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE')
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


settings = Settings()
