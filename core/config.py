# core/config.py
import os
import json

GREEN = "#4cc26e"
YELLOW = "#f0b232"
RED = "#e84a5f"
TEXT_MUTED = "#8a8a8a"
BG_MAIN = "#1e1e1e"
BG_SEC = "#2b2b2b"
TEXT_MAIN = "#dbdee1"
BLURPLE = "#5865F2"

CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".material_manager_config.json")

def load_config() -> dict:
    """Carica la configurazione utente dal file JSON."""
    if not os.path.exists(CONFIG_FILE_PATH): 
        return {}
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f: 
            return json.load(f)
    except (json.JSONDecodeError, IOError): 
        return {}

def save_config(config: dict) -> None:
    """Salva la configurazione utente."""
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f: 
            json.dump(config, f, indent=4)
    except IOError: 
        pass