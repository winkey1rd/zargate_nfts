import os
from pydantic_settings import BaseSettings

_env = os.getenv("PYTHON_ENV", "")
_env_files: tuple[str, ...] = (
    f".env{f'.{_env}' if _env else ''}",
    f"../../.env{f'.{_env}' if _env else ''}",  # корень монорепо
)


class DbSettings(BaseSettings):
    """Настройки подключения к PostgreSQL. Читает переменные с префиксом DB_."""

    model_config = {"env_file": _env_files, "env_prefix": "DB_", "extra": "allow"}

    driver: str = "postgresql+asyncpg"
    server: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        return (
            f"{self.driver}://{self.user}:{self.password}"
            f"@{self.server}:{self.port}/{self.name}"
        )


class Ports(BaseSettings):
    """Порты сервисов. Без префикса — имена совпадают с env vars напрямую."""

    model_config = {"env_file": _env_files, "extra": "allow"}

    api_port: int = 8000
    db_port: int = 5432