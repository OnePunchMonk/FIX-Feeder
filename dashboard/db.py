import yaml
import sqlite3
import psycopg2
import psycopg2.extras

def get_db_connection():
    """Reads the main config and connects to the configured database."""
    with open("./config/config.yml", "r") as f:
        config = yaml.safe_load(f)

    storage_config = config['storage']
    
    if storage_config['type'] == 'postgresql':
        pg_config = storage_config['postgres_config']
        conn = psycopg2.connect(
            user=pg_config['user'],
            password=pg_config['password'],
            host=pg_config['host'],
            port=pg_config['port'],
            database=pg_config['database'],
            cursor_factory=psycopg2.extras.DictCursor
        )
    elif storage_config['type'] == 'sqlite':
        conn = sqlite3.connect(storage_config['path'])
        conn.row_factory = sqlite3.Row
    else:
        raise ValueError("Unsupported database type in config for dashboard")
        
    return conn