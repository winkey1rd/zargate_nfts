from pydantic_settings import BaseSettings, SettingsConfigDict

from nft_shared.config.settings_base import DbSettings, _env_files


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files("bot/.env"),
        extra="ignore",
    )

    db: DbSettings = DbSettings()

    bot_token: str
    admin_telegram_ids: list[int] = []


settings = Settings()