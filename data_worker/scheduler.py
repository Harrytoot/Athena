import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from redis import Redis

from data_worker.config import REDIS_URL
from data_worker.sync import sync_market_overview, sync_stock_list

logger = logging.getLogger(__name__)


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

    scheduler.add_job(
        sync_stock_list,
        CronTrigger(hour=8, minute=30),
        args=[redis_client],
        id="sync_stock_list",
        name="Sync stock list",
    )

    scheduler.add_job(
        sync_market_overview,
        CronTrigger(hour=15, minute=30, day_of_week="mon-fri"),
        args=[redis_client],
        id="sync_market_overview",
        name="Sync market overview",
    )

    logger.info("Scheduler configured: stock_list@08:30, market_overview@15:30 mon-fri")
    return scheduler
