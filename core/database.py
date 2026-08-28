import sqlite3
import pathlib
from utils.helpers import local_app_data_dir

DB_PATH = local_app_data_dir() / "nova_database.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    schema = """
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT,
        email TEXT,
        age TEXT,
        role TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS app_config (
        config_key TEXT PRIMARY KEY,
        config_value TEXT
    );

    CREATE TABLE IF NOT EXISTS ai_providers (
        provider_id TEXT PRIMARY KEY,
        api_url TEXT,
        api_key TEXT,
        model TEXT,
        is_active BOOLEAN DEFAULT 0
    );
    """
    with get_connection() as conn:
        conn.executescript(schema)
        conn.commit()

# Ensure the database is initialized when this module is imported.
init_db()
