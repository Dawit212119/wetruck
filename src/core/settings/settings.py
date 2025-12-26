from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
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
    database_url: Optional[str] = None
    access_token_expire_minutes: int = 60
    jwt_secret_key: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    s3_bucket_name: str = ""
    s3_region: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    @model_validator(mode='after')
    def construct_database_url(self):
        """Construct database_url from individual fields if not provided"""
        if not self.database_url and self.db_host and self.db_name:
            self.database_url = (
                f"postgresql://{self.db_username}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return self

    model_config = SettingsConfigDict(env_file=".env")
  

settings = Settings()