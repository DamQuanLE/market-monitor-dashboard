import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
CONFIG_PATH = ROOT_DIR / "config.yaml"
DB_PATH = DATA_DIR / "market_monitor.db"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    log_path = LOG_DIR / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


def load_config() -> Dict[str, Any]:
    load_dotenv()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / previous * 100.0


def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True, default=str)


def flatten_assets(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for asset_class, assets in config.get("assets", {}).items():
        for name, meta in assets.items():
            entry = {"name": name, "asset_class": asset_class}
            entry.update(meta)
            items.append(entry)
    return items
