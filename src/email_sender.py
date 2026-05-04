from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict

from .utils import get_env


def _smtp_config() -> Dict[str, Any]:
    return {
        "host": get_env("EMAIL_HOST"),
        "port": int(get_env("EMAIL_PORT", "587")),
        "user": get_env("EMAIL_USER"),
        "password": get_env("EMAIL_PASSWORD"),
        "to": get_env("EMAIL_TO"),
    }


def send_email(subject: str, body: str) -> None:
    cfg = _smtp_config()
    if not cfg["host"] or not cfg["user"] or not cfg["password"] or not cfg["to"]:
        raise RuntimeError("Missing SMTP configuration in .env")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["user"]
    msg["To"] = cfg["to"]
    msg.set_content(body)

    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.send_message(msg)


def send_alert_email(alert: Dict[str, Any]) -> None:
    subject = f"Market Alert: {alert.get('asset_name')} - {alert.get('alert_type')}"
    body = (
        f"Asset: {alert.get('asset_name')}\n"
        f"Alert: {alert.get('alert_type')}\n"
        f"Price: {alert.get('price')}\n"
        f"Reason: {alert.get('message')}\n"
        f"Timestamp: {alert.get('triggered_at')}\n"
        "\nOpen the dashboard for details."
    )
    send_email(subject, body)


def send_daily_digest(report: str) -> None:
    send_email("Daily Market Monitor Report", report)


def test_email() -> None:
    send_email("Market Monitor Test Email", "This is a test email from Market Monitor Dashboard.")
