import json
import os

from dotenv import load_dotenv
from confluent_kafka import Consumer

from storage.minio.minio import MinioService
from storage.mongo.mongoservice import MongoService
from storage.kafka.producer import Producer

from processing.cleaning.clean import clean_text
from processing.transform.sentiment_analysis import PredictSentimen

load_dotenv()


class NLPConsumer:

    def __init__(self):

        self.base_topics = [
            "stocks_news",
            "crypto_news",
            "forex_news"
        ]

        self.raw_topics = [
            f"raw_{topic}"
            for topic in self.base_topics
        ]

        self.consumer = Consumer({
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092"
            ),
            "group.id": os.getenv(
                "KAFKA_GROUP_ID",
                "nlp-group"
            ),
            "auto.offset.reset": "earliest",
        })

        self.consumer.subscribe(self.raw_topics)

        self.minio = MinioService("raw-news")
        self.mongo = MongoService()

        self.producers = {}
        self.models = {}

    def get_producer(self, base_topic):

        silver_topic = f"silver_{base_topic}"

        if silver_topic not in self.producers:

            self.producers[silver_topic] = Producer(
                brokers=os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS",
                    "localhost:9092"
                ),
                topic=silver_topic
            )

        return self.producers[silver_topic]

    def get_model(self, category):

        category = (category or "general").lower()

        if category not in self.models:

            self.models[category] = PredictSentimen(
                category
            )

        return self.models[category]

    def get_article(self, storage_path):

        response = self.minio.client.get_object(
            bucket_name=self.minio.bucket_name,
            object_name=storage_path
        )

        data = json.loads(
            response.read().decode()
        )

        response.close()
        response.release_conn()

        return data

    def process_message(self, msg):

        data = json.loads(
            msg.value().decode()
        )

        raw_topic = msg.topic()

        base_topic = raw_topic.replace(
            "raw_",
            ""
        )

        producer = self.get_producer(
            base_topic
        )

        article = self.get_article(
            data["storage_path"]
        )

        text = article.get(
            "text",
            ""
        )

        metadata = article.get(
            "metadata",
            {}
        )

        category = metadata.get(
            "category",
            base_topic
        )

        clean = clean_text(text)

        model = self.get_model(category)

        result = model.predict_with_score(
            clean[:512]
        )

        nlp_result = {
            "raw_topic": raw_topic,
            "silver_topic": f"silver_{base_topic}",
            "category": category,
            "text_clean": clean,
            "sentiment": result
        }

        self.mongo.update_nlp_result(
            url_hash=data["url_hash"],
            nlp_result=nlp_result
        )

        producer.send({
            "url": data["url"],
            "url_hash": data["url_hash"],
            "raw_topic": raw_topic,
            "silver_topic": f"silver_{base_topic}",
            "category": category,
            "sentiment": result,
            "text_clean": clean
        })

        print(
            f"SUCCESS | "
            f"{raw_topic} -> silver_{base_topic} | "
            f"sentiment={result.get('label')}"
        )

    def run(self):

        try:

            while True:

                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():

                    print(
                        "KAFKA ERROR:",
                        msg.error()
                    )

                    continue

                try:

                    self.process_message(msg)

                except Exception as e:

                    print(
                        "PROCESS ERROR:",
                        e
                    )

        except KeyboardInterrupt:

            print("STOPPED")

        finally:

            self.consumer.close()


if __name__ == "__main__":

    NLPConsumer().run()