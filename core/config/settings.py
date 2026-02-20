from functools import lru_cache
from typing import Optional

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
      Configuration settings for the REST API.

      This class defines environment variables and default settings for the API, database,
      JWT authentication, email configuration, and additional variables. Settings are loaded
      from a .env file with case-sensitive keys.

      IMPORTANT: Sensitive values (passwords, secrets, keys) should ONLY be defined
      in the .env file and NOT have default values here for security reasons.
    """

    # ==================== API Configuration ====================
    API_NAME: str = "MIIT_API"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_STR: str = "v1"
    API_VERSION_NUM: str = "0.0.50"
    API_LOG_LEVEL: str = "DEBUG"
    APP_LOG_DIR: str = "/var/www/metalteco/log/app_logs"

    ALLOWED_HOSTS: list[str] = [
        "integrador.turbograneles.com",
        "informes.turbograneles.com",
        "localhost:8000",
        "localhost:5173",
    ]
    CORS_ORIGINS: list[str] = [
        "https://informes.turbograneles.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # ==================== API Super User (SENSITIVE) ====================
    # These values MUST be set via .env file
    API_USER_ADMINISTRATOR: str
    API_PASSWORD_ADMINISTRATOR: SecretStr

    # ==================== Database Configuration (SENSITIVE) ====================
    DB_TYPE: str = "PostgreSQL"
    DB_USER: str  # Required from .env
    DB_PASSWORD: SecretStr  # Required from .env
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str  # Required from .env

    # ==================== Email Configuration (SENSITIVE) ====================
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: str = "587"
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None

    # ==================== JWT Configuration (SENSITIVE) ====================
    JWT_SECRET_KEY: SecretStr  # Required from .env
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 40
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    JWT_ISSUER: str = "MIIT-API-Authentication"
    JWT_AUDIENCE: str = "MIIT-API"

    # ==================== Encryption (SENSITIVE) ====================
    ENCRYPTION_KEY: SecretStr  # Required from .env

    # ==================== Feature Configuration ====================
    # Despacho Directo - Almacenamiento Virtual
    ALMACENAMIENTO_DESPACHO_DIRECTO_ID: int = 0

    # ==================== External API: TurboGraneles (SENSITIVE) ====================
    TG_API_AUTH: str = ""
    TG_API_URL: str = ""
    TG_API_USER: Optional[str] = None
    TG_API_PASS: Optional[SecretStr] = None
    TG_API_ACCEPTS_LIST: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore',
        # Fail fast if required env vars are missing
        validate_default=True,
    )


@lru_cache
def get_settings():
    return Settings()