"""Scheduler process: python -m worker.main"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.db import SessionLocal
from app.logging_setup import setup_logging
from app.services.notifier import set_notifier
from worker import jobs

log = logging.getLogger(__name__)


def _wrap(job):
    async def runner():
        try:
            async with SessionLocal() as session:
                n = await job(session)
                if n:
                    log.info("%s: %s item(s)", job.__name__, n)
        except Exception:
            log.exception("Job %s failed", job.__name__)

    runner.__name__ = job.__name__
    return runner


async def main() -> None:
    setup_logging()
    if settings.telegram_bot_token:
        from bot.main import build_bot
        from bot.telegram_notifier import TelegramNotifier

        set_notifier(TelegramNotifier(build_bot()))
    else:
        log.warning("TELEGRAM_BOT_TOKEN missing: notifications are only logged")
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(_wrap(jobs.send_reminders), "interval", minutes=1, max_instances=1, coalesce=True)
    scheduler.add_job(_wrap(jobs.expire_pending), "interval", minutes=5, max_instances=1, coalesce=True)
    scheduler.add_job(_wrap(jobs.auto_complete), "interval", minutes=10, max_instances=1, coalesce=True)
    scheduler.add_job(_wrap(jobs.expire_quote_requests), "interval", hours=1, max_instances=1, coalesce=True)
    scheduler.add_job(_wrap(jobs.pro_daily_agenda), "interval", minutes=10, max_instances=1, coalesce=True)
    scheduler.start()
    log.info("Worker started")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
