from pydantic_settings import BaseSettings, SettingsConfigDict

from nft_shared.config.settings_base import DbSettings, _env_files


class FetchSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FETCH_",
        extra="ignore",
    )

    interval_seconds: int = 3600
    semaphore_size: int = 10


class RetrySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RETRY_",
        extra="ignore",
    )

    seconds_429: int = 300      # rate limit от TON API
    seconds_5xx: int = 30       # серверная ошибка
    seconds_network: int = 5    # сетевая ошибка
    max_attempts: int = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files("fetcher/.env"),
        extra="ignore",
    )

    db: DbSettings = DbSettings()
    fetch: FetchSettings = FetchSettings()
    retry: RetrySettings = RetrySettings()


settings = Settings()