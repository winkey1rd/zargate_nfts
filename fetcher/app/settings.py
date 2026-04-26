from pydantic_settings import BaseSettings

from nft_shared.config.settings_base import DbSettings, _env_files


class Settings(BaseSettings):
    model_config = {"env_file": _env_files, "extra": "allow"}

    db: DbSettings = DbSettings()

    # Интервалы запуска задач
    fetch_interval_seconds: int = 3600      # полный fetch всех коллекций
    price_check_interval_seconds: int = 300 # обновление цен через GetGems

    # Параллельность
    fetch_semaphore_size: int = 10          # макс. одновременных запросов к TON API

    # Retry по типу ошибки
    retry_429_seconds: int = 300            # rate limit от TON — ждём 5 минут
    retry_5xx_seconds: int = 30            # серверная ошибка — ждём 30 секунд
    retry_network_seconds: int = 5         # сетевая ошибка — ждём 5 секунд
    retry_max_attempts: int = 3


settings = Settings()