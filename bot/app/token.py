import hashlib
import hmac
import os


def _get_secret() -> str:
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        raise RuntimeError("SECRET_KEY env var is not set")
    return secret


def generate_token(telegram_id: int, wallet_address: str) -> str:
    """
    Детерминированный HMAC-SHA256 токен.

    Свойства:
    - Привязан к паре (telegram_id, wallet_address) — нельзя использовать
      токен одного кошелька для другого.
    - Без срока действия — перевыдаётся только явно через /mytoken.
    - Верифицируется без обращения к БД (опционально).

    Формат: hex string, 64 символа.
    """
    message = f"{telegram_id}|{wallet_address}".encode()
    secret = _get_secret().encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verify_token(token: str, telegram_id: int, wallet_address: str) -> bool:
    """Константное сравнение — защита от timing attack."""
    expected = generate_token(telegram_id, wallet_address)
    return hmac.compare_digest(expected, token)