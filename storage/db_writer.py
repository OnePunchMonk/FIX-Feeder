import sqlite3
import psycopg2
import logging
import json # Import the json library
from datetime import datetime

class DBWriter:
    def __init__(self, config):
        self.type = config['type']
        self.logger = logging.getLogger(__name__)
        if self.type == 'sqlite':
            # check_same_thread=False is needed for multi-threaded access by the socket listener
            self.conn = sqlite3.connect(config['path'], check_same_thread=False)
            self._create_table_sqlite()
        elif self.type == 'postgresql':
            pg_config = config['postgres_config']
            self.conn = psycopg2.connect(
                user=pg_config['user'],
                password=pg_config['password'],
                host=pg_config['host'],
                port=pg_config['port'],
                database=pg_config['database']
            )
            self._create_table_postgres()

    def _create_table_sqlite(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fix_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_seq_num INTEGER,
                sending_time TEXT,
                message TEXT
            )
        ''')
        self.conn.commit()

    def _create_table_postgres(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fix_messages (
                id SERIAL PRIMARY KEY,
                msg_seq_num INTEGER,
                sending_time TIMESTAMP,
                message JSONB
            )
        ''')
        self.conn.commit()

    def write(self, message):
        cursor = self.conn.cursor()
        msg_seq_num = message.get(34)
        sending_time_str = message.get(52)

        sending_time_obj = None
        if sending_time_str:
            try:
                if '.' in sending_time_str:
                    sending_time_obj = datetime.strptime(sending_time_str, '%Y%m%d-%H:%M:%S.%f')
                else:
                    sending_time_obj = datetime.strptime(sending_time_str, '%Y%m%d-%H:%M:%S')
            except ValueError:
                self.logger.warning(f"Could not parse timestamp: {sending_time_str}")
        
        # --- THIS IS THE FIX ---
        # Serialize the message dictionary to a valid JSON string
        message_json = json.dumps(message)
        # --- END OF FIX ---

        if self.type == 'sqlite':
            cursor.execute("INSERT INTO fix_messages (msg_seq_num, sending_time, message) VALUES (?, ?, ?)",
                           (msg_seq_num, sending_time_obj.isoformat() if sending_time_obj else None, message_json))
        elif self.type == 'postgresql':
            # Pass the valid JSON string, psycopg2 handles JSONB insertion automatically
            cursor.execute("INSERT INTO fix_messages (msg_seq_num, sending_time, message) VALUES (%s, %s, %s)",
                           (msg_seq_num, sending_time_obj, message_json))
        self.conn.commit()
        self.logger.debug("Wrote message to database.")