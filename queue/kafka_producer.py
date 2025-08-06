import json
import logging
from kafka import KafkaProducer as KafkaClient

class KafkaProducer:
    def __init__(self, config):
        self.enabled = config['enabled']
        if self.enabled:
            self.producer = KafkaClient(
                bootstrap_servers=config['brokers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.topic = config['topic']
        self.logger = logging.getLogger(__name__)

    def send(self, message):
        if self.enabled:
            self.producer.send(self.topic, message)
            self.logger.debug(f"Sent message to Kafka topic {self.topic}")

    def close(self):
        if self.enabled:
            self.producer.close()