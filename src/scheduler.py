from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


_scheduler: BackgroundScheduler | None = None


def start_scheduler(digest_job: Callable[[], None], daily_time: str) -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    hour, minute = daily_time.split(":")
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(digest_job, "cron", hour=int(hour), minute=int(minute))
    _scheduler.start()
    logger.info("Scheduler started for daily digest at %s", daily_time)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
