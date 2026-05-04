from __future__ import annotations

from typing import Any, Dict

from .alpha_vantage_provider import AlphaVantageProvider
from .databento_provider import DatabentoProvider
from .fred_provider import FredProvider
from .finnhub_provider import FinnhubProvider
from .ibkr_provider import IbkrProvider
from .twelve_data_provider import TwelveDataProvider
from .yfinance_provider import YFinanceProvider


def get_provider(config: Dict[str, Any]):
    default_provider = config["data"]["default_provider"]
    providers = config["data"]["providers"]

    if default_provider == "yfinance":
        refresh = providers["yfinance"].get("refresh_interval_seconds", 60)
        return YFinanceProvider(refresh_interval_seconds=refresh)

    if default_provider == "fred":
        return FredProvider(api_key_env=providers["fred"]["api_key_env"])

    if default_provider == "alpha_vantage":
        return AlphaVantageProvider(api_key_env=providers["alpha_vantage"]["api_key_env"])

    if default_provider == "ibkr":
        cfg = providers["ibkr"]
        return IbkrProvider(cfg["host"], cfg["port"], cfg["client_id"])

    if default_provider == "twelve_data":
        return TwelveDataProvider(api_key_env=providers["twelve_data"]["api_key_env"])

    if default_provider == "finnhub":
        return FinnhubProvider(api_key_env=providers["finnhub"]["api_key_env"])

    if default_provider == "databento":
        return DatabentoProvider(api_key_env=providers["databento"]["api_key_env"])

    return YFinanceProvider(refresh_interval_seconds=60)
