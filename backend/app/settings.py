import os

from pydantic_settings import BaseSettings

env = os.getenv("PYTHON_ENV")


class GlobalSettings(BaseSettings):
    class Config:
        env_file: tuple = (
            f'.env{f".{env}" if env else ""}',
            f'./api/.env{f".{env}" if env else ""}')
        extra: str = 'allow'

class DbSettings(GlobalSettings):
    db_driver: str
    db_server: str
    db_name: str
    db_user: str
    db_password: str
    url: str = ''

class Ports(GlobalSettings):
    api_port: int
    db_port: int

class Settings(GlobalSettings):
    ports: Ports = Ports()
    db_settings: DbSettings = DbSettings()

settings = Settings()
db_settings = settings.db_settings
settings.db_settings.url = f'{db_settings.db_driver}://{db_settings.db_user}:{db_settings.db_password}@{db_settings.db_server}:{settings.db_port}/{db_settings.db_name}'
