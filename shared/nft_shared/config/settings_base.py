import os
from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = os.getenv("PYTHON_ENV", "dev")


def _env_files(*extra: str) -> tuple[str, ...]:
    """
    Возвращает кортеж путей к env файлам для данного сервиса.
    extra — пути к сервис-специфичным файлам относительно корня проекта.

    Пример для api:
        _env_files("api/.env")
        → (".env.dev", "api/.env.dev")
    """
    root = f".env.{_ENV}"
    service = tuple(f"{path}.{_ENV}" for path in extra)
    return root, *service


class DbSettings(BaseSettings):
    """
    Настройки PostgreSQL.
    """
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        extra="ignore",
    )

    driver: str = "postgresql+asyncpg"
    host: str
    port: int
    name: str
    user: str
    password: str

    @cached_property
    def url(self) -> str:
        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """
    Настройки Redis.
    """
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = "redis"
    port: int = 6379
    db: int = 0

    @cached_property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class Ports(BaseSettings):
    """
    Порты сервисов.
    """
    model_config = SettingsConfigDict(extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1