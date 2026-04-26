"""scheduler.py — APScheduler задачи"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from nft_shared.db.session import build_engine, build_session_factory
from fetcher.app.fetch_service import fetch_all_collections
from fetcher.app.settings import settings

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncIOScheduler:
    engine = build_engine(settings.db.url)
    session_factory = build_session_factory(engine)

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        fetch_all_collections,
        trigger=IntervalTrigger(seconds=settings.fetch_interval_seconds),
        args=[session_factory],
        id="fetch_all_collections",
        replace_existing=True,
        max_instances=1,      # не запускать повторно если предыдущий ещё идёт
        coalesce=True,
    )

    return scheduler