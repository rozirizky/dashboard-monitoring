import json
import logging
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

from minio import Minio

from app.api.core.config import settings

logger = logging.getLogger(__name__)


class MinioService:
    def __init__(self, bucket: str):
        self.bucket_name = bucket
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("Bucket created: %s", self.bucket_name)
        except Exception:
            logger.exception("Failed to ensure bucket '%s'", self.bucket_name)
            raise

    def upload_json(self, category: str, data: dict) -> dict | None:
        today = datetime.now(timezone.utc)
        object_name = (
            f"{category}/"
            f"{today.year}/{today.month:02d}/{today.day:02d}/"
            f"{uuid4()}.json"
        )
        try:
            payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BytesIO(payload),
                length=len(payload),
                content_type="application/json",
            )
            logger.debug("Uploaded: %s", object_name)
            return {"bucket": self.bucket_name, "object_name": object_name}
        except Exception:
            logger.exception("Upload failed: %s", object_name)
            return None

    def delete(self, object_name: str) -> bool:
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info("Deleted: %s", object_name)
            return True
        except Exception:
            logger.exception("Delete failed: %s", object_name)
            return False
