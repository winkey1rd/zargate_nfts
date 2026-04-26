import logging
from typing import List, Tuple

import aiohttp

from nft_shared.models.extra import MonitorRule
from nft_shared.models.nft import NftBaseORM
from nft_shared.models.sticker import StickerORM
from monitor.app.settings import settings

logger = logging.getLogger(__name__)

TG_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_notification(
    chat_id: int,
    rule: MonitorRule,
    matches: List[Tuple[StickerORM, NftBaseORM]],
) -> None:
    lines = [f"🔔 <b>Уведомление мониторинга</b> (правило #{rule.id}, тип: {rule.rule_type})\n"]

    for sticker, nft in matches[:10]:  # не более 10 в одном сообщении
        price_str = f"{nft.price:.2f} TON" if nft.price else "—"
        ratio_str = ""
        if nft.price and sticker.total_value:
            ratio_str = f" | ratio: {nft.price / sticker.total_value:.3f}"
        lines.append(
            f"• <a href='https://getgems.io/nft/{nft.address}'>{nft.name}</a> "
            f"— {price_str}{ratio_str} | PWR: {sticker.total_value}"
        )

    if len(matches) > 10:
        lines.append(f"\n…и ещё {len(matches) - 10} стикеров.")

    text = "\n".join(lines)

    async with aiohttp.ClientSession() as http:
        url = TG_API.format(token=settings.notification_bot_token)
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        async with http.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                logger.error(f"Telegram API error {resp.status}: {body}")