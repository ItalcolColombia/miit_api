from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
      Configuration settings for the REST API.

      This class defines environment variables and default settings for the API, database,
      JWT authentication, email configuration, and additional variables. Settings are loaded
      from a .env file with case-sensitive keys.

    """
    #API Params
    API_NAME: str = "MIIT_API"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = "8000"
    API_V1_STR: str = "v1"
    API_VERSION_NUM: str = "0.0.27"
    API_LOG_LEVEL: str = "DEBUG"
    APP_LOG_DIR: str = "/var/www/metalteco/log/app_logs"
    ALLOWED_HOSTS: list[str] = ["*"]

    # API 'SU' Params
    API_USER_ADMINISTRATOR: str = "administrator"
    API_PASSWORD_ADMINISTRATOR: str = "$2b$12$XZpenPj7tndIasZhG5FS9OP.fmKJlUs2pOPw3oH/SmYQ9q07A7o7C"

    # Database Params
    DB_TYPE: str = "PostgreSQL"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "M3t4l867s0ft"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "PTOAntioquia_DW"

    #Email Params
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: str = "587"
    SMTP_USER: str = "usuario"
    SMTP_PASSWORD: str = "clave"

    # JWT Params
    JWT_SECRET_KEY: str = "nS3-_u1K93UkTlg_RsGCPGLF8oPhFKN_h8z0G4LWSTk"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 40
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    JWT_ISSUER: str = "MIIT-API-Authentication"
    JWT_AUDIENCE: str = "MIIT-API"

    #Aditional Params
    ENCRYPTION_KEY:str="5o5POG_5KxOpY3ztmwrKn6Y4kF16B4xoyEKHWoYERZw="

    # TurboGraneles API
    TG_API_AUTH:str = ""
    TG_API_URL:str = "http://turbograneles-puertoantioquia-424798204.us-east-1.elb.amazonaws.com"
    TG_API_USER:str = "daniel.pacheco@metalteco.com"
    TG_API_PASS:str ="Passw0rd_metalteco"
    TG_API_ACCEPTS_LIST: bool = True


    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'ignore'


@lru_cache
def get_settings():
    return Settings()