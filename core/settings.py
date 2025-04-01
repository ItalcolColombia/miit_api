from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    #Api settings
    API_NAME: str
    API_VERSION: str
    API_HOST: str
    API_PORT: int
    API_VERSION: str
    API_LOG_LEVEL: str
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

    #@property
    # def DATABASE_URL(self) -> str:
    #     return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()