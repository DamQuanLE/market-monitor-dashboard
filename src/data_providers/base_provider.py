from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List


class BaseProvider(ABC):
    @abstractmethod
    def get_latest_price(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_historical_data(
        self,
        asset: Dict[str, Any],
        start_date: str | None,
        end_date: str | None,
        interval: str,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def stream_prices(self, asset_list: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_provider_status(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def is_realtime(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_latency(self) -> float | None:
        raise NotImplementedError
