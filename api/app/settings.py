from pydantic_settings import BaseSettings

from nft_shared.config.settings_base import DbSettings, Ports, _env_files


class Settings(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    db: DbSettings = DbSettings()
    ports: Ports = Ports()

    redis_url: str = "redis://redis:6379/0"
    secret_key: str

    # Rate limit
    rate_limit_ip_rpm: int = 60
    rate_limit_ip_burst: int = 20
    rate_limit_token_warn: int = 30   # предупреждение (заголовок X-Rate-Warning)
    rate_limit_token_block: int = 60  # блок (429)


settings = Settings()