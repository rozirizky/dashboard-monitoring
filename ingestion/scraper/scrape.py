import asyncio
import hashlib
import logging
import traceback
from datetime import datetime, timezone
from urllib.parse import urlsplit

from ingestion.scraper.extractor import Extractor
from ingestion.scraper.parsing import Parser
from storage.kafka.producer import Producer
from storage.minio.minio import MinioService
from storage.mongo.mongoservice import MongoService

from app.api.core.config import settings

logger = logging.getLogger(__name__)


class Scrape:
    def __init__(self):
        self.extract = Extractor()
        self.parser = Parser()
        self.mongo = MongoService()
        self.minio = MinioService(settings.MINIO_BUCKET)

    def close(self):
        self.mongo.close()

    async def _process_url(
        self,
        url: dict,
        metadata_base: dict,
        producer: Producer,
        semaphore: asyncio.Semaphore,
    ) -> str:
        async with semaphore:
            link = url.get("link")
            if not link:
                return "failed"

            try:
                url_hash = hashlib.md5(link.encode()).hexdigest()

                if await asyncio.to_thread(self.mongo.url_exists, url_hash):
                    logger.debug("Duplicate URL skipped: %s", link)
                    return "duplicate"

                html = await asyncio.to_thread(self.extract.news, link)
                if not html:
                    logger.warning("Failed to fetch article: %s", link)
                    return "failed"

                data = await self.parser.get_content(html)
                if not data:
                    logger.warning("Failed to parse content: %s", link)
                    return "failed"

                content = data.get("text", "")
                if not content or not content.strip():
                    logger.warning("Empty content, skipping: %s", link)
                    return "failed"

                content_hash = hashlib.md5(content.encode()).hexdigest()

                if await asyncio.to_thread(self.mongo.content_exists, content_hash):
                    logger.debug("Duplicate content skipped: %s", link)
                    return "duplicate"

                metadata = {
                    **metadata_base,
                    "url": link,
                    "url_hash": url_hash,
                    "content_hash": content_hash,
                    "title": data.get("title"),
                    "author": data.get("author"),
                    "date": data.get("date"),
                    "crawl_time": datetime.now(timezone.utc).isoformat(),
                }
                data["metadata"] = metadata

                storage = await asyncio.to_thread(
                    self.minio.upload_json,
                    category=metadata["category"],
                    data=data,
                )
                if not storage:
                    logger.error("MinIO upload failed: %s", link)
                    return "failed"

                try:
                    await asyncio.to_thread(
                        self.mongo.insert_raw_metadata,
                        kafka_data=metadata,
                        storage_result=storage,
                    )
                except Exception as mongo_err:
                    logger.error("MongoDB insert failed, rolling back MinIO: %s | %s", link, mongo_err)
                    logger.debug(traceback.format_exc())
                    try:
                        await asyncio.to_thread(self.minio.delete, storage.get("object_name"))
                        logger.info("MinIO rollback success: %s", storage.get("object_name"))
                    except Exception as rollback_err:
                        logger.error("MinIO rollback failed: %s", rollback_err)
                    return "failed"

                producer.send({
                    "source_id": metadata["source_id"],
                    "url_hash": url_hash,
                    "storage_path": storage["object_name"],
                })

                logger.info("Success: %s", link)
                return "success"

            except Exception:
                logger.exception("Unexpected error processing '%s'", link)
                return "failed"

    async def news(self, source) -> bool:
        base_url = source.baseurl
        topic = f"raw_{source.kafka_topic}"
        source_name = source.source

        if not topic or not base_url:
            logger.error("Missing topic or source URL in config")
            return False

        producer = Producer(topic=topic)

        html = await asyncio.to_thread(self.extract.news, base_url)
        if not html:
            logger.error("Failed to fetch listing page: %s", base_url)
            return False

        urls = await self.parser.get_url(html, base_url)
        if not urls:
            logger.warning("No relevant URLs found from: %s", source_name)
            return False

        logger.info("Processing %d URLs from %s", len(urls), source_name)

        metadata_base = {
            "source_id": source.id,
            "source": source_name,
            "domain": urlsplit(base_url).netloc,
            "topic": topic,
            "category": source.category,
            "language": source.language,
            "country": source.country,
        }

        semaphore = asyncio.Semaphore(settings.SCRAPE_CONCURRENCY)

        results = await asyncio.gather(
            *[self._process_url(url, metadata_base, producer, semaphore) for url in urls]
        )

        success = results.count("success")
        duplicate = results.count("duplicate")
        failed = results.count("failed")

        flushed = await asyncio.to_thread(producer.flush, 30)
        if flushed > 0:
            logger.warning("[%s] %d Kafka messages failed delivery", source_name, flushed)

        logger.info(
            "Done [%s] | success=%d duplicate=%d failed=%d",
            source_name, success, duplicate, failed,
        )
        return True
