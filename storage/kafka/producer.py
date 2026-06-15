import json
import logging

from confluent_kafka import Producer as KafkaProducer

from app.api.core.config import settings

logger = logging.getLogger(__name__)


class Producer:
    def __init__(self, topic: str):
        self.topic = topic
        self.producer = KafkaProducer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "message.timeout.ms": 30000,
            "acks": "all",
        })

    def _on_delivery(self, err, msg):
        if err:
            logger.error("Delivery failed [%s]: %s", self.topic, err)
        else:
            logger.debug(
                "Delivered to %s [%d] offset=%d",
                msg.topic(), msg.partition(), msg.offset(),
            )

    def send(self, data: dict) -> None:
        self.producer.produce(
            self.topic,
            value=json.dumps(data),
            callback=self._on_delivery,
        )
        self.producer.poll(0)

    def flush(self, timeout: int = 30) -> int:
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning("%d messages not delivered after %ds", remaining, timeout)
        return remaining
