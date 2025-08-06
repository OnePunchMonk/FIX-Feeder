import logging
import time

class FileReader:
    def __init__(self, config, parser, producer, db_writer):
        self.file_path = config['file_path']
        self.parser = parser
        self.producer = producer
        self.db_writer = db_writer
        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info(f"Starting file reader for {self.file_path}")
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    message = line.strip()
                    if message:
                        parsed_message = self.parser.parse(message)
                        if parsed_message:
                            self.producer.send(parsed_message)
                            self.db_writer.write(parsed_message)
        except FileNotFoundError:
            self.logger.error(f"File not found: {self.file_path}")
        except Exception as e:
            self.logger.error(f"An error occurred while reading the file: {e}")
        finally:
            self.logger.info("Finished reading file.")