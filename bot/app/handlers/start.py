import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from nft_shared.models.user import Wallet
from nft_shared.crud.wallet_repository import WalletRepository
from bot.app.token import generate_token

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session):
    """
    /start <wallet_address>

    Если кошелёк уже зарегистрирован — возвращает существующий токен.
    Если нет — создаёт Wallet и выдаёт новый токен.
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажи адрес кошелька:\n"
            "<code>/start UQ...</code>",
            parse_mode="HTML",
        )
        return

    wallet_address = args[1].strip()
    telegram_id = message.from_user.id
    username = message.from_user.username

    repo = WalletRepository(session)

    # Проверяем, нет ли уже кошелька с таким telegram_id
    existing = await repo.get_by_telegram_id(telegram_id)
    if existing:
        await message.answer(
            f"Ты уже зарегистрирован.\n"
            f"Твой токен:\n<code>{existing.token}</code>",
            parse_mode="HTML",
        )
        return

    token = generate_token(telegram_id, wallet_address)

    wallet = Wallet(
        address=wallet_address,
        telegram_id=telegram_id,
        telegram_username=username,
        token=token,
        # Флаги по умолчанию — базовый доступ
        is_synergy=True,
        is_portfolio=True,
        is_basket_show=True,
        is_new_portfolio=True,
        is_basket_add=False,
        is_all_stickers_show=False,
        is_opening=False,
    )
    await repo.create(wallet)
    await session.commit()

    logger.info(f"New wallet registered: {wallet_address} (tg_id={telegram_id})")

    await message.answer(
        f"✅ Регистрация успешна!\n\n"
        f"Кошелёк: <code>{wallet_address}</code>\n\n"
        f"Твой токен (не передавай никому):\n"
        f"<code>{token}</code>\n\n"
        f"Используй этот токен в приложении: X-Token заголовок.",
        parse_mode="HTML",
    )


@router.message(lambda m: m.text == "/mytoken")
async def cmd_mytoken(message: Message, session):
    """Повторная выдача токена по telegram_id."""
    repo = WalletRepository(session)
    wallet = await repo.get_by_telegram_id(message.from_user.id)
    if not wallet:
        await message.answer("Кошелёк не найден. Зарегистрируйся через /start UQ...")
        return
    await message.answer(
        f"Твой токен:\n<code>{wallet.token}</code>",
        parse_mode="HTML",
    )