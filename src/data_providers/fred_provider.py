from __future__ import annotations

import logging
from datetime import timezone
from typing import Any, Dict, Iterable, List

import requests

from ..utils import get_env
from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class FredProvider(BaseProvider):
    def __init__(self, api_key_env: str) -> None:
        self.api_key = get_env(api_key_env)

    def get_latest_price(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        series_id = asset.get("fred_symbol")
        if not series_id or not self.api_key:
            return {}
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("observations"):
            return {}
        obs = data["observations"][0]
        ts = obs["date"] + "T00:00:00+00:00"
        value = float(obs["value"]) if obs["value"] not in (".", None) else None
        return {
            "timestamp": ts,
            "last_price": value,
            "bid": None,
            "ask": None,
            "volume": None,
            "provider": "fred",
            "latency_seconds": None,
        }

    def get_historical_data(
        self,
        asset: Dict[str, Any],
        start_date: str | None,
        end_date: str | None,
        interval: str,
    ) -> List[Dict[str, Any]]:
        series_id = asset.get("fred_symbol")
        if not series_id or not self.api_key:
            return []
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date or "1900-01-01",
            "observation_end": end_date,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        rows: List[Dict[str, Any]] = []
        for obs in data.get("observations", []):
            value = float(obs["value"]) if obs["value"] not in (".", None) else None
            ts = obs["date"] + "T00:00:00+00:00"
            rows.append(
                {
                    "timestamp": ts,
                    "open": value,
                    "high": value,
                    "low": value,
                    "close": value,
                    "volume": None,
                }
            )
        return rows

    def stream_prices(self, asset_list: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        logger.info("FRED does not support streaming. Returning empty stream.")
        return []

    def get_provider_status(self) -> Dict[str, Any]:
        return {
            "name": "fred",
            "mode": "daily",
            "status": "ok" if self.api_key else "missing_api_key",
            "realtime": False,
        }

    def is_realtime(self) -> bool:
        return False

    def get_latency(self) -> float | None:
        return None
