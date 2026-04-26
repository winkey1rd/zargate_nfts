import asyncio
import logging

from fetcher.app.scheduler import build_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Fetcher scheduler started")

    # Запускаем первый fetch сразу при старте
    scheduler.get_job("fetch_all_collections").modify(next_run_time=__import__("datetime").datetime.now())

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Fetcher scheduler stopped")


if __name__ == "__main__":
    asyncio.run(main())