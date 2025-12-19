from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Class to hold variables settings.
    """
    db_host: str = ""
    db_name: str = ""          # Added type annotation
    db_username: str = ""      # Added type annotation
    db_port: int = 5321
    db_password: str = ""      # Added type annotation (or Optional[str] if it can be None)

    model_config = SettingsConfigDict(env_file=".env")
    # You can add more config here if needed, e.g.:
    # model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, case_sensitive=False)

settings = Settings()