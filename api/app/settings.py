from pydantic_settings import BaseSettings, SettingsConfigDict

from nft_shared.config.settings_base import DbSettings, RedisSettings, Ports, _env_files


class RateLimitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        extra="ignore",
    )

    ip_rpm: int = 60
    ip_burst: int = 20
    token_warn: int = 30
    token_block: int = 60


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files("api/.env.dev"),
        extra="ignore",
    )

    secret_key: str

    db: DbSettings = DbSettings()
    redis: RedisSettings = RedisSettings()
    ports: Ports = Ports()
    rate_limit: RateLimitSettings = RateLimitSettings()


settings = Settings()