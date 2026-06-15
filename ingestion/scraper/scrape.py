import asyncio
import hashlib
import logging
import os
import traceback
from datetime import datetime, timezone
from urllib.parse import urlsplit

from dotenv import load_dotenv

from ingestion.scraper.extractor import Extractor
from ingestion.scraper.parsing import Parser
from storage.kafka.producer import Producer
from storage.minio.minio import MinioService
from storage.mongo.mongoservice import MongoService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

MAX_CONCURRENT = int(os.getenv("SCRAPE_CONCURRENCY", "5"))


class Scrape:
    def __init__(self):
        self.extract = Extractor()
        self.parser = Parser()
        self.mongo = MongoService()
        self.minio = MinioService("raw-news")
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
                    logger.debug(f"Duplikat URL dilewati: {link}")
                    return "duplicate"

                html_news = await asyncio.to_thread(self.extract.news, link)
                if not html_news:
                    logger.warning(f"Gagal fetch artikel: {link}")
                    return "failed"

                data = await self.parser.get_content(html_news)
                if not data:
                    logger.warning(f"Gagal parse konten: {link}")
                    return "failed"

                content = data.get("text", "")
                if not content or not content.strip():
                    logger.warning(f"Konten kosong, skip: {link}")
                    return "failed"

                content_hash = hashlib.md5(content.encode()).hexdigest()

                if not url_hash or not content_hash:
                    logger.error(f"Hash kosong, skip: {link}")
                    return "failed"

                if await asyncio.to_thread(self.mongo.content_exists, content_hash):
                    logger.debug(f"Duplikat konten dilewati: {link}")
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
                    logger.error(f"Gagal upload MinIO: {link}")
                    return "failed"

                try:
                    await asyncio.to_thread(
                        self.mongo.insert_raw_metadata,
                        kafka_data=metadata,
                        storage_result=storage,
                    )
                except Exception as mongo_err:
                    logger.error(f"Gagal insert MongoDB, rollback MinIO: {link} | {mongo_err}")
                    logger.debug(traceback.format_exc())
                    try:
                        await asyncio.to_thread(self.minio.delete, storage.get("object_name"))
                        logger.info(f"Rollback MinIO berhasil: {storage.get('object_name')}")
                    except Exception as rollback_err:
                        logger.error(f"Rollback MinIO gagal: {rollback_err}")
                    return "failed"

                producer.send({
                    "source_id": metadata["source_id"],
                    "url_hash": url_hash,
                    "storage_path": storage["object_name"],
                })

                logger.info(f"Berhasil: {link}")
                return "success"

            except Exception as e:
                logger.error(f"Error saat proses '{link}': {e}")
                logger.debug(traceback.format_exc())
                return "failed"

    async def news(self, news) -> bool:
        source = news.baseurl
        topic = f"raw_{news.kafka_topic}"
        source_name = news.source

        if not topic or not source:
            logger.error("Topic/source tidak ditemukan di config")
            return False

        producer = Producer(topic=topic)

        html = await asyncio.to_thread(self.extract.news, source)
        if not html:
            logger.error(f"Gagal fetch listing page: {source}")
            return False

        urls = await self.parser.get_url(html, source)
        if not urls:
            logger.warning(f"Tidak ada URL relevan dari: {source_name}")
            return False

        logger.info(f"Mulai proses {len(urls)} URL dari {source_name}")

        metadata_base = {
            "source_id": news.id,
            "source": source_name,
            "domain": urlsplit(source).netloc,
            "topic": topic,
            "category": news.category,
            "language": news.language,
            "country": news.country,
        }

        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        results = await asyncio.gather(*[
            self._process_url(url, metadata_base, producer, semaphore)
            for url in urls
        ])

        success = results.count("success")
        duplicate = results.count("duplicate")
        failed = results.count("failed")

        flushed = await asyncio.to_thread(producer.flush, 30)
        if flushed > 0:
            logger.warning(f"[{source_name}] {flushed} pesan Kafka gagal terkirim")

        logger.info(
            f"Selesai [{source_name}] | "
            f"success={success} duplicate={duplicate} failed={failed}"
        )
        return True
