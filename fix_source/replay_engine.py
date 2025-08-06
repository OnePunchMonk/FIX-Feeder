import logging
import time

class ReplayEngine:
    def __init__(self, config, parser, producer, db_writer):
        self.file_path = config['file_path']
        self.speed_multiplier = config.get('speed_multiplier', 1.0)
        self.parser = parser
        self.producer = producer
        self.db_writer = db_writer
        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info(f"Starting replay engine for {self.file_path} at {self.speed_multiplier}x speed")
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    message = line.strip()
                    if message:
                        parsed_message = self.parser.parse(message)
                        if parsed_message:
                            self.producer.send(parsed_message)
                            self.db_writer.write(parsed_message)
                            # Simulate delay
                            time.sleep(1 / self.speed_multiplier)
        except FileNotFoundError:
            self.logger.error(f"Replay file not found: {self.file_path}")
        except Exception as e:
            self.logger.error(f"An error occurred during replay: {e}")
        finally:
            self.logger.info("Replay finished.")