import asyncio
import logging

from ingestion.scraper.scrape import Scrape
from app.api.db.session import AsyncSessionLocal
from app.api.services.source_service import NewsSourceService

MAX_CONCURRENT_SOURCES = 2

logger = logging.getLogger(__name__)


async def run_source(scrape: Scrape, source) -> None:
    logger.info("Starting: %s (priority=%s)", source.source, source.priority)
    try:
        result = await scrape.news(source)
        logger.info("Done: %s | success=%s", source.source, result)
    except Exception:
        logger.exception("Error processing source: %s", source.source)


async def main() -> None:
    scrape = Scrape()
    try:
        async with AsyncSessionLocal() as db:
            sources = await NewsSourceService.get_source_by_priority(db)

            if not sources:
                logger.warning("No active sources found")
                return

            logger.info("Total active sources: %s", len(sources))

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_SOURCES)

            async def worker(source):
                async with semaphore:
                    await run_source(scrape, source)

            await asyncio.gather(*(worker(s) for s in sources))
    finally:
        scrape.close()

    logger.info("All sources processed")


if __name__ == "__main__":
    asyncio.run(main())
