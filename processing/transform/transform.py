import asyncio
import hashlib
import json
import logging

from dateutil import parser
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError, KafkaException

load_dotenv()

from storage.minio.minio import MinioService
from processing.cleaning.clean import clean_text
from processing.transform.translate import Translate
from processing.transform.sentiment_analysis import PredictSentimen
from processing.transform.extract_features import extract_keywords, summarize
from app.api.db.session import AsyncSessionLocal
from app.api.services.article_service import ArticleService
from app.api.core.config import settings

logger = logging.getLogger(__name__)

BASE_TOPICS = ["stocks_news", "crypto_news", "forex_news"]
POLL_TIMEOUT = 1.0


class Transform:
    def __init__(self):
        self.raw_topics = [f"raw_{t}" for t in BASE_TOPICS]

        self.consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "nlp-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        self.consumer.subscribe(self.raw_topics)

        self.minio = MinioService(settings.MINIO_BUCKET)
        self.translator = Translate()
        self._models: dict[str, PredictSentimen] = {}

        logger.info("Transform initialized. Topics=%s", self.raw_topics)

    def _get_model(self, category: str) -> PredictSentimen:
        key = (category or "stocks").lower()
        if key not in self._models:
            logger.info("Loading sentiment model: %s", key)
            self._models[key] = PredictSentimen(key)
        return self._models[key]

    def _fetch_article(self, storage_path: str) -> dict:
        response = self.minio.client.get_object(
            bucket_name=self.minio.bucket_name,
            object_name=storage_path,
        )
        try:
            return json.loads(response.read().decode())
        finally:
            response.close()
            response.release_conn()

    def _translate_if_needed(self, text: str, language: str) -> str:
        if language == "en":
            return text
        return self.translator.translate_text(text)

    def _analyze(self, content: str, title: str, category: str, language: str):
        translated_content = self._translate_if_needed(content, language)
        translated_title = self._translate_if_needed(title, language)

        sentiment = self._get_model(category).predict_with_score(translated_content)
        tags = [item["keyword"] for item in extract_keywords(translated_content, translated_title)]
        summary = summarize(translated_content, translated_title)

        return sentiment, tags, summary

    async def _process_message(self, msg) -> None:
        payload = json.loads(msg.value().decode())

        storage_path = payload.get("storage_path")
        if not storage_path:
            logger.warning("storage_path missing in message")
            return

        if not payload.get("source_id"):
            logger.warning("source_id missing in message")
            return

        article = self._fetch_article(storage_path)
        text = article.get("text", "")
        metadata = article.get("metadata", {})

        if not text.strip():
            logger.warning("Empty article at path: %s", storage_path)
            return

        clean_content = clean_text(text)
        sentiment, tags, summary = self._analyze(
            content=clean_content,
            title=metadata.get("title", ""),
            category=metadata.get("category", "stocks"),
            language=metadata.get("language", "en"),
        )

        article_data = {
            "source_id": payload.get("source_id"),
            "url_hash": payload.get("url_hash"),
            "content_hash": hashlib.md5(clean_content.encode()).hexdigest(),
            "url": metadata.get("url"),
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "content": clean_content,
            "language": metadata.get("language"),
            "category": metadata.get("category"),
            "topic": metadata.get("topic"),
            "country": metadata.get("country"),
            "published_date": parser.parse(metadata["date"]) if metadata.get("date") else None,
        }

        nlp_data = {
            "sentiment_label": sentiment.get("label"),
            "confidence_score": sentiment.get("confidence"),
            "summary": summary,
            "tags": tags,
        }

        storage_data = {
            "bucket": self.minio.bucket_name,
            "object_name": storage_path,
        }

        async with AsyncSessionLocal() as session:
            try:
                await ArticleService(session).insert(
                    article_data=article_data,
                    nlp_data=nlp_data,
                    storage_data=storage_data,
                )
            except Exception:
                await session.rollback()
                raise

        logger.info("Saved article: %s", article_data["url_hash"])

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        logger.info("Starting consume loop")
        try:
            while True:
                msg = self.consumer.poll(POLL_TIMEOUT)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                try:
                    await self._process_message(msg)
                    self.consumer.commit(message=msg, asynchronous=False)
                except Exception:
                    logger.exception("Failed processing offset=%s", msg.offset())
                    self.consumer.commit(message=msg, asynchronous=False)

        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.consumer.close()
            logger.info("Consumer closed")


if __name__ == "__main__":
    Transform().run()
