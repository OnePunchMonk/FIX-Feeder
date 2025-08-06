#import argparse
import time
import yaml
import logging
from protocol_parsers.fix_parser import FixParser
from queue.kafka_producer import KafkaProducer
from storage.db_writer import DBWriter

OFFSET_FILE = 'replay.offset'

def save_offset(line_num):
    with open(OFFSET_FILE, 'w') as f:
        f.write(str(line_num))

def load_offset():
    try:
        with open(OFFSET_FILE, 'r') as f:
            return int(f.read().strip())
    except (IOError, ValueError):
        return 0

def replay(args):
    with open("config/config.yml", "r") as f:
        config = yaml.safe_load(f)

    logging.basicConfig(level=config['core']['log_level'])
    logger = logging.getLogger("ReplayCLI")
    
    parser = FixParser(config.get('filter'))
    db_writer = DBWriter(config['storage'])
    kafka_producer = KafkaProducer(config['queue'])

    start_line = 0
    if args.recover:
        start_line = load_offset()
        logger.info(f"Recovering replay from line {start_line + 1}")

    logger.info(f"Starting replay of '{args.file}' at {args.speed}x speed.")
    
    try:
        with open(args.file, 'r') as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue # Skip lines until we reach the offset
                
                message = line.strip()
                if message:
                    parsed = parser.parse(message)
                    if parsed:
                        kafka_producer.send(parsed)
                        db_writer.write(parsed)
                        logger.info(f"Processed line {i+1}")
                
                save_offset(i + 1)
                time.sleep(1 / args.speed)
                
    except FileNotFoundError:
        logger.error(f"File not found: {args.file}")
    except KeyboardInterrupt:
        logger.info("\nReplay interrupted. Offset saved. Re-run with --recover to continue.")
    finally:
        logger.info("Replay finished.")


if __name__ == "__main__":
    cli_parser = argparse.ArgumentParser(description="FixFeeder Replay Tool")
    cli_parser.add_argument('--file', required=True, help="Path to the FIX log file to replay.")
    cli_parser.add_argument('--speed', type=float, default=1.0, help="Speed multiplier for replay (e.g., 2.0 for 2x speed).")
    cli_parser.add_argument('--recover', action='store_true', help="Recover from the last processed line.")
    
    args = cli_parser.parse_args()
    replay(args)