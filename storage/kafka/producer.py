import json
import logging
import os

from confluent_kafka import Producer as KafkaProducer
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Producer:
    def __init__(self, topic: str):
        self.topic = topic

        conf = {
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            "message.timeout.ms": 30000,
            "acks": "all",
        }

        self.producer = KafkaProducer(conf)

    def _delivery_report(self, err, msg):
        if err:
            logger.error(f"Delivery failed: {err}")
        else:
            logger.info(
                f"Delivered to {msg.topic()} "
                f"[{msg.partition()}] offset={msg.offset()}"
            )

    def send(self, data: dict) -> None:
        self.producer.produce(
            self.topic,
            value=json.dumps(data),
            callback=self._delivery_report,
        )
        self.producer.poll(0)

    def flush(self, timeout: int = 30) -> int:
        logger.info("Flushing Kafka producer...")
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning(f"{remaining} pesan tidak terkirim setelah {timeout}s")
        else:
            logger.info("Flush selesai, semua pesan terkirim")
        return remaining
