import os

from pydantic_settings import BaseSettings

env = os.getenv("PYTHON_ENV")


class GlobalSettings(BaseSettings):
    class Config:
        env_file: tuple = (
            f'.env{f".{env}" if env else ""}',
            f'./api/.env{f".{env}" if env else ""}')
        extra: str = 'allow'

class Settings(GlobalSettings):
    api_port: int
    db_port: int
    db_name: str

settings = Settings()
