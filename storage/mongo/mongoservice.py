import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from loguru import logger
from pymongo import MongoClient, ReturnDocument

load_dotenv()


class MongoService:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[os.getenv("MONGO_DATABASE")]
        self.collection = self.db["raw_news_metadata"]
        self.create_indexes()

    def source_news(self) -> list[dict]:
        return list(
            self.db["source_news"].find(
                {"source": {"$regex": "Valbury Forex", "$options": "i"}},
                {"_id": 0},
            )
        )

    def create_indexes(self) -> None:
        self.collection.create_index("content_hash", unique=True)
        self.collection.create_index("url_hash", unique=True)
        self.collection.create_index("article.url")

    def url_exists(self, url_hash: str) -> bool:
        return self.collection.count_documents({"url_hash": url_hash}, limit=1) > 0

    def content_exists(self, content_hash: str) -> bool:
        return self.collection.count_documents({"content_hash": content_hash}, limit=1) > 0

    def insert_raw_metadata(self, kafka_data: dict, storage_result: dict) -> None:
        document = {
            "url_hash": kafka_data.get("url_hash"),
            "content_hash": kafka_data.get("content_hash"),
            "source": {
                "name": kafka_data.get("source"),
                "domain": kafka_data.get("domain"),
            },
            "article": {
                "title": kafka_data.get("title"),
                "author": kafka_data.get("author"),
                "url": kafka_data.get("url"),
                "category": kafka_data.get("category"),
                "language": kafka_data.get("language"),
                "published_date": kafka_data.get("date"),
            },
            "storage": storage_result,
            "created_at": datetime.now(timezone.utc),
        }
        self.collection.insert_one(document)
        logger.success("Mongo insert success")

    def update_nlp_result(self, url_hash: str, nlp_result: dict) -> bool:
        result = self.collection.find_one_and_update(
            {"url_hash": url_hash},
            {
                "$set": {
                    "nlp": {
                        "sentiment": nlp_result.get("sentiment"),
                        "text_clean": nlp_result.get("text_clean"),
                        "processed_at": nlp_result.get("processed_at"),
                    },
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        if not result:
            logger.warning(f"Dokumen tidak ditemukan untuk update | url_hash={url_hash}")
            return False

        logger.debug(f"NLP result tersimpan | url_hash={url_hash}")
        return True

    def close(self) -> None:
        if self.client:
            self.client.close()
