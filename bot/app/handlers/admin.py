import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from nft_shared.crud.wallet_repository import WalletRepository

logger = logging.getLogger(__name__)
router = Router()

ALLOWED_FLAGS = {
    "is_synergy", "is_portfolio", "is_basket_show",
    "is_new_portfolio", "is_basket_add", "is_all_stickers_show", "is_opening",
}

# Telegram ID администраторов (задаётся в env)
import os
ADMIN_IDS: set[int] = {
    int(x) for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip()
}


@router.message(Command("flag"))
async def cmd_flag(message: Message, session):
    """
    /flag <wallet_address> <flag_name> <0|1>

    Пример: /flag UQAbc... is_basket_add 1
    """
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет прав.")
        return

    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("Использование: /flag <wallet> <flag_name> <0|1>")
        return

    _, wallet_address, flag_name, flag_value = parts

    if flag_name not in ALLOWED_FLAGS:
        await message.answer(f"❌ Неизвестный флаг. Доступные: {', '.join(sorted(ALLOWED_FLAGS))}")
        return

    if flag_value not in ("0", "1"):
        await message.answer("❌ Значение флага должно быть 0 или 1.")
        return

    repo = WalletRepository(session)
    wallet = await repo.get_by_address(wallet_address)
    if not wallet:
        await message.answer(f"❌ Кошелёк {wallet_address} не найден.")
        return

    setattr(wallet, flag_name, flag_value == "1")
    await session.commit()

    status = "✅ включён" if flag_value == "1" else "❌ выключен"
    await message.answer(
        f"Флаг <b>{flag_name}</b> для кошелька <code>{wallet_address}</code> {status}.",
        parse_mode="HTML",
    )
    logger.info(f"Admin {message.from_user.id} set {flag_name}={flag_value} for {wallet_address}")