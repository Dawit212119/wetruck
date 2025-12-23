from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.core.settings.env import Environment


class Settings(BaseSettings):
    """
    Class to hold variables settings.
    """
    env: Environment = Environment.DEV
    db_host: str = ""
    db_name: str = ""          
    db_username: str = ""     
    db_port: int = 5321
    db_password: str = ""     
    access_token_expire_minutes: int = 60
    jwt_secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"


    model_config = SettingsConfigDict(env_file=".env")
  

settings = Settings()