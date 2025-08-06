import logging
from kafka import KafkaConsumer as KafkaClient

class KafkaConsumer:
    def __init__(self, config, parser, producer, db_writer, shutdown_event):
        self.parser = parser
        self.producer = producer  # The producer for parsed messages
        self.db_writer = db_writer
        self.logger = logging.getLogger(__name__)
        self.shutdown_event = shutdown_event
        
        self.consumer = KafkaClient(
            config['kafka_topic'],
            bootstrap_servers=config['kafka_brokers'],
            auto_offset_reset='earliest',
            group_id='fixfeeder_raw_consumer',
            consumer_timeout_ms=1000  # Timeout to avoid blocking forever
        )

    def start(self):
        self.logger.info(f"Starting Kafka consumer for topic {self.consumer.topics()}")
        while not self.shutdown_event.is_set():
            try:
                # The poll() will block for max 1000ms (consumer_timeout_ms)
                for message in self.consumer:
                    raw_message = message.value.decode('utf-8')
                    self.logger.debug(f"Received raw message from Kafka: {raw_message}")
                    parsed_message = self.parser.parse(raw_message)
                    if parsed_message:
                        self.producer.send(parsed_message)
                        self.db_writer.write(parsed_message)
            except Exception as e:
                self.logger.error(f"Error in Kafka consumer loop: {e}")

        self.consumer.close()
        self.logger.info("Kafka consumer has shut down.")