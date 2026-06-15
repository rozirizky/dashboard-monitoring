from datetime import datetime, timezone
from uuid import uuid4
from io import BytesIO
import json
import os
from dotenv import load_dotenv
load_dotenv()
from minio import Minio
from loguru import logger


class MinioService:
    def __init__(self, bucket: str):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )
        self.bucket_name = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket created: {self.bucket_name}")
            else:
                logger.debug(f"Bucket already exists: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Gagal memastikan bucket '{self.bucket_name}': {e}")
            raise
   # storage/minio/minio.py
    def delete(self, object_name: str) -> bool:
        try:
            self.client.remove_object(self.bucket_name, object_name)  # ← self.bucket_name
            logger.info(f"Delete success: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Gagal delete objek MinIO '{object_name}': {e}")
            return False

    def upload_json(self, category: str, data: dict) -> dict | None:
        try:
            today = datetime.now(timezone.utc)
            object_name = (
                f"{category}/"
                f"{today.year}/"
                f"{today.month:02d}/"
                f"{today.day:02d}/"
                f"{uuid4()}.json"
            )

            json_bytes = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BytesIO(json_bytes),
                length=len(json_bytes),
                content_type="application/json",
            )

            logger.success(f"Upload success: {object_name}")
            return {
                "bucket": self.bucket_name,
                "object_name": object_name,
            }

        except Exception as e:
            logger.error(f"Gagal upload ke MinIO '{object_name}': {e}")
            return None