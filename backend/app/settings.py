import os
from pydantic_settings import BaseSettings

env = os.getenv("PYTHON_ENV")

_env_files: tuple = (
    f'.env{f".{env}" if env else ""}',
    f'./api/.env{f".{env}" if env else ""}',
)


class DbSettings(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    db_driver: str
    db_server: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int


class Ports(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    api_port: int
    db_port: int


class Settings(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    ports: Ports = Ports()
    db: DbSettings = DbSettings()

    @property
    def db_url(self) -> str:
        return (
            f"{self.db.db_driver}://{self.db.db_user}:{self.db.db_password}"
            f"@{self.db.db_server}:{self.db.db_port}/{self.db.db_name}"
        )


settings = Settings()