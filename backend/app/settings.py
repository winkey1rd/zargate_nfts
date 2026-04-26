import os
from pydantic_settings import BaseSettings

_env = os.getenv("PYTHON_ENV", "")
_env_files = (
    f".env{f'.{_env}' if _env else ''}",
    f"./backend/.env{f'.{_env}' if _env else ''}",
)


class Settings(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    db_driver: str = "postgresql+asyncpg"
    db_server: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    redis_url: str = "redis://redis:6379/0"

    api_port: int = 8000
    secret_key: str

    rate_limit_ip_rpm: int = 60
    rate_limit_ip_burst: int = 20
    rate_limit_token_warn: int = 30
    rate_limit_token_block: int = 60

    @property
    def db_url(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_password}"
            f"@{self.db_server}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
