import json
from core.database import get_connection

APP_VERSION = "1.0"

def load_config() -> dict:
    defaults = {
        "autosave": True,
        "font_size": 13,
    }
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT config_key, config_value FROM app_config")
            rows = cursor.fetchall()
            for row in rows:
                try:
                    defaults[row["config_key"]] = json.loads(row["config_value"])
                except json.JSONDecodeError:
                    defaults[row["config_key"]] = row["config_value"]
    except Exception:
        pass
    return defaults

def save_config(cfg: dict) -> None:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for key, value in cfg.items():
                val_str = json.dumps(value)
                cursor.execute("""
                    INSERT INTO app_config (config_key, config_value)
                    VALUES (?, ?)
                    ON CONFLICT(config_key) DO UPDATE SET config_value=excluded.config_value
                """, (key, val_str))
            conn.commit()
    except Exception as e:
        print(f"Error saving config: {e}")
