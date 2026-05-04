from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .database import fetch_alert_history, insert_alert_history
from .email_sender import send_alert_email

logger = logging.getLogger(__name__)


def _cooldown_active(asset_id: int, alert_type: str, cooldown_hours: int) -> bool:
    history = fetch_alert_history(limit=200)
    for row in history:
        if row["asset_id"] == asset_id and row["alert_type"] == alert_type:
            if row["cooldown_until"]:
                cooldown_until = datetime.fromisoformat(row["cooldown_until"])
                return cooldown_until > datetime.now(timezone.utc)
    return False


def _record_alert(asset_id: int, alert_type: str, message: str, price: float, cooldown_hours: int) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    cooldown_until = now + timedelta(hours=cooldown_hours)
    entry = {
        "asset_id": asset_id,
        "alert_type": alert_type,
        "message": message,
        "price": price,
        "triggered_at": now.isoformat(),
        "email_sent": False,
        "cooldown_until": cooldown_until.isoformat(),
    }
    insert_alert_history(entry)
    return entry


def trigger_alerts(
    asset_id: int,
    asset_name: str,
    last_price: float,
    signals: Dict[str, Any],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not config["alerts"]["enabled"]:
        return []

    cooldown_hours = config["alerts"].get("cooldown_hours", 6)
    triggered: List[Dict[str, Any]] = []

    for alert_type, should_trigger in signals.items():
        if not should_trigger:
            continue
        if _cooldown_active(asset_id, alert_type, cooldown_hours):
            continue
        message = f"{asset_name}: {alert_type} triggered at {last_price:.4f}"
        entry = _record_alert(asset_id, alert_type, message, last_price, cooldown_hours)
        if config["alerts"].get("email_enabled"):
            try:
                send_alert_email({**entry, "asset_name": asset_name})
                entry["email_sent"] = True
            except Exception as exc:  # noqa: BLE001
                logger.exception("Email alert failed: %s", exc)
        triggered.append(entry)

    return triggered
