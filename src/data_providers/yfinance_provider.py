from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

import yfinance as yf

from .base_provider import BaseProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(BaseProvider):
    def __init__(self, refresh_interval_seconds: int = 60) -> None:
        self.refresh_interval_seconds = refresh_interval_seconds
        self._latency_seconds: float | None = None

    def get_latest_price(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        symbol = asset.get("yahoo_symbol") or asset.get("symbol")
        if not symbol:
            return {}
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="2d", interval="1d")
        if data.empty:
            return {}
        last_row = data.iloc[-1]
        timestamp = last_row.name.to_pydatetime().replace(tzinfo=timezone.utc)
        return {
            "timestamp": timestamp.isoformat(),
            "last_price": float(last_row["Close"]),
            "bid": None,
            "ask": None,
            "volume": float(last_row.get("Volume", 0.0)),
            "provider": "yfinance",
            "latency_seconds": None,
        }

    def get_historical_data(
        self,
        asset: Dict[str, Any],
        start_date: str | None,
        end_date: str | None,
        interval: str,
    ) -> List[Dict[str, Any]]:
        symbol = asset.get("yahoo_symbol") or asset.get("symbol")
        if not symbol:
            return []
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        if data.empty:
            return []
        rows: List[Dict[str, Any]] = []
        for idx, row in data.iterrows():
            ts = idx.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            rows.append(
                {
                    "timestamp": ts.isoformat(),
                    "open": float(row.get("Open", 0.0)),
                    "high": float(row.get("High", 0.0)),
                    "low": float(row.get("Low", 0.0)),
                    "close": float(row.get("Close", 0.0)),
                    "volume": float(row.get("Volume", 0.0)),
                }
            )
        return rows

    def stream_prices(self, asset_list: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        logger.info("YFinance does not support streaming. Returning empty stream.")
        return []

    def get_provider_status(self) -> Dict[str, Any]:
        return {
            "name": "yfinance",
            "mode": "polling",
            "status": "ok",
            "realtime": False,
        }

    def is_realtime(self) -> bool:
        return False

    def get_latency(self) -> float | None:
        return self._latency_seconds
