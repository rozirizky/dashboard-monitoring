import logging
from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval   import IntervalTrigger

from app.api.db.session import sync_engine
from app.api.models.market   import Base
from ingestion.market_price import (
    fetch_crypto_trending,
    fetch_crypto_markets,
    fetch_stocks,
    fetch_forex,
    cleanup_old_data,
    run_all,
)

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main():
    
    log.info("🗄  Memastikan schema PostgreSQL sudah ada…")
    Base.metadata.create_all(sync_engine)
    log.info("✅  Schema OK")

    
    log.info("🚀  Initial fetch on startup…")
    run_all()

    scheduler = BlockingScheduler(timezone="Asia/Jakarta")

    scheduler.add_job(
        fetch_crypto_trending,
        trigger       = IntervalTrigger(minutes=10),
        id            = "cg_trending",
        name          = "CoinGecko Trending",
        max_instances = 1,
        coalesce      = True,
        misfire_grace_time = 120,
    )
    scheduler.add_job(
        fetch_crypto_markets,
        trigger       = IntervalTrigger(minutes=15),
        id            = "cg_markets",
        name          = "CoinGecko Markets",
        max_instances = 1,
        coalesce      = True,
        misfire_grace_time = 120,
    )
    scheduler.add_job(
        fetch_stocks,
        trigger       = IntervalTrigger(minutes=5),
        id            = "yf_stocks",
        name          = "Yahoo Finance Stocks",
        max_instances = 1,
        coalesce      = True,
        misfire_grace_time = 60,
    )
    scheduler.add_job(
        fetch_forex,
        trigger       = IntervalTrigger(minutes=5),
        id            = "forex",
        name          = "Forex Rates",
        max_instances = 1,
        coalesce      = True,
        misfire_grace_time = 60,
    )
    scheduler.add_job(
        cleanup_old_data,
        trigger       = IntervalTrigger(hours=6),
        id            = "cleanup",
        name          = "Cleanup Old Data",
        max_instances = 1,
    )

    log.info("⏰  Scheduler started — Ctrl+C to stop")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    main()