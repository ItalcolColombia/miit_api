from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    #Api settings
    API_NAME: str
    API_V1_STR: str
    API_HOST: str
    API_PORT: int
    API_VERSION: str
    API_LOG_LEVEL: str
    APP_LOG_DIR: str = "/var/www/metalteco/log/app_logs"
    API_USER_ADMINISTRATOR: str
    API_PASSWORD_ADMINISTRATOR: str

    # Database settings
    DB_TYPE: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    JWT_ISSUER: str = "MIIT"
    JWT_AUDIENCE: str = "MIIT-API"

    #Aditional vars
    ENCRYPTION_KEY:str

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()