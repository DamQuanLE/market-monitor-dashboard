from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .base_provider import BaseProvider


class DatabentoProvider(BaseProvider):
    def __init__(self, api_key_env: str) -> None:
        self.api_key_env = api_key_env

    def get_latest_price(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_historical_data(
        self,
        asset: Dict[str, Any],
        start_date: str | None,
        end_date: str | None,
        interval: str,
    ) -> List[Dict[str, Any]]:
        return []

    def stream_prices(self, asset_list: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        return []

    def get_provider_status(self) -> Dict[str, Any]:
        return {"name": "databento", "mode": "websocket", "status": "not_implemented", "realtime": True}

    def is_realtime(self) -> bool:
        return True

    def get_latency(self) -> float | None:
        return None
