import yaml
import logging
import signal
from threading import Thread, Event
from prometheus_client import start_http_server

from fix_source.socket_listener import SocketListener
from fix_source.file_reader import FileReader
from fix_source.kafka_consumer import KafkaConsumer
from protocol_parsers.fix_parser import FixParser
from queue.kafka_producer import KafkaProducer
from storage.db_writer import DBWriter
from dashboard import app as dashboard_app

# --- Graceful Shutdown Handling ---
shutdown_event = Event()

def shutdown_handler(signum, frame):
    logging.info("Shutdown signal received, stopping services...")
    shutdown_event.set()
# --------------------------------

def main():
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)

    logging.basicConfig(level=config['core']['log_level'])
    logger = logging.getLogger(__name__)

    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Initialize components
    parser = FixParser(config.get('filter'))
    db_writer = DBWriter(config['storage'])
    kafka_producer = KafkaProducer(config['queue'])

    if config['monitoring']['enabled']:
        start_http_server(config['monitoring']['prometheus_port'])
        logger.info(f"Prometheus server started on port {config['monitoring']['prometheus_port']}")

    source_type = config['source']['type']
    logger.info(f"Starting FIX source of type: {source_type}")

    source = None
    # Pass the shutdown_event to the listener
    if source_type == 'socket':
        source = SocketListener(config['source'], parser, kafka_producer, db_writer, shutdown_event)
    elif source_type == 'file':
        source = FileReader(config['source'], parser, kafka_producer, db_writer)
    elif source_type == 'kafka':
        source = KafkaConsumer(config['source'], parser, kafka_producer, db_writer, shutdown_event)
    else:
        logger.error(f"Unsupported source type: {source_type}")
        return

    source_thread = Thread(target=source.start)
    source_thread.start()

    if config['dashboard']['enabled']:
        dashboard_thread = Thread(target=lambda: dashboard_app.run(host=config['dashboard']['host'], port=config['dashboard']['port']))
        dashboard_thread.daemon = True
        dashboard_thread.start()
        logger.info(f"Dashboard/API running on http://{config['dashboard']['host']}:{config['dashboard']['port']}")
    
    logger.info("FixFeeder is running. Press Ctrl+C to exit.")
    
    # Wait for the source thread to finish or for a shutdown signal
    while source_thread.is_alive():
        if shutdown_event.is_set():
            break
        time.sleep(0.1)

    # Clean up resources
    logger.info("Cleaning up resources...")
    kafka_producer.close()
    db_writer.close()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    import time
    main()