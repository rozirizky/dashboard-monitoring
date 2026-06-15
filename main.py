import asyncio
import logging

from ingestion.scraper.scrape import Scrape
from app.api.db.session import AsyncSessionLocal
from app.api.services.source_service import NewsSourceService

MAX_CONCURRENT_SOURCES = 2

logger = logging.getLogger(__name__)


async def run_source(scrape: Scrape, source):
    logger.info(
        "Mulai: %s (priority=%s)",
        source.source,
        source.priority,
    )

    try:
        result = await scrape.news(source)

        logger.info(
            "Selesai: %s | sukses=%s",
            source.source,
            result,
        )

    except Exception:
        logger.exception(
            "Error saat proses source: %s",
            source.source,
        )


async def main():
    scrape = Scrape()
    
    try:
            

        async with AsyncSessionLocal() as db:

            sources = await NewsSourceService.get_source_by_priority(db)
        
            if not sources:
                logger.warning("Tidak ada source aktif ditemukan")
                return

            logger.info(
                "Total source aktif: %s",
                len(sources),
            )

            semaphore = asyncio.Semaphore(
                MAX_CONCURRENT_SOURCES
            )

            async def worker(source):
                async with semaphore:
                    await run_source(scrape, source)

            await asyncio.gather(
                *(worker(source) for source in sources)
            )
    finally:
        scrape.close()

    logger.info("Semua source selesai diproses")


if __name__ == "__main__":
    asyncio.run(main())