from pydantic_settings import BaseSettings, SettingsConfigDict

from nft_shared.config.settings_base import DbSettings, _env_files


class CheckSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHECK_",
        extra="ignore",
    )

    interval_seconds: int = 300


class NotifySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    notification_bot_token: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files("monitor/.env"),
        extra="ignore",
    )

    db: DbSettings = DbSettings()
    check: CheckSettings = CheckSettings()
    notify: NotifySettings = NotifySettings()


settings = Settings()