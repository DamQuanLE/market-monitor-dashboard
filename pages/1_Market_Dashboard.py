from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:  # noqa: BLE001
    st_autorefresh = None

from src.alerts import trigger_alerts
from src.data_providers.provider_factory import get_provider
from src.database import init_db, upsert_asset, upsert_latest_price
from src.email_sender import test_email
from src.indicators import (
    bollinger_bands,
    daily_returns,
    drawdown,
    moving_average,
    rsi,
    realized_volatility,
    trend_classification,
)
from src.utils import flatten_assets, load_config, pct_change, safe_float


def _period_to_dates(period: str) -> tuple[str | None, str | None]:
    end = datetime.now(timezone.utc)
    if period == "1D":
        start = end - timedelta(days=1)
    elif period == "5D":
        start = end - timedelta(days=5)
    elif period == "1M":
        start = end - timedelta(days=30)
    elif period == "3M":
        start = end - timedelta(days=90)
    elif period == "6M":
        start = end - timedelta(days=180)
    elif period == "YTD":
        start = datetime(end.year, 1, 1, tzinfo=timezone.utc)
    elif period == "1Y":
        start = end - timedelta(days=365)
    elif period == "5Y":
        start = end - timedelta(days=365 * 5)
    else:
        return None, None
    return start.date().isoformat(), end.date().isoformat()


@st.cache_data(ttl=300)
def _fetch_class_summary(assets: List[Dict[str, Any]], _provider) -> pd.DataFrame:
    rows = []
    for asset in assets:
        latest = _provider.get_latest_price(asset)
        if not latest:
            continue
        last_price = latest.get("last_price")
        rows.append(
            {
                "asset": asset["name"],
                "last_price": last_price,
                "provider": latest.get("provider", "n/a"),
                "last_update": latest.get("timestamp"),
            }
        )
    return pd.DataFrame(rows)


def _calc_change(df: pd.DataFrame, days: int) -> float:
    if df.empty or "close" not in df.columns:
        return 0.0
    if len(df) <= days:
        return 0.0
    return pct_change(df["close"].iloc[-1], df["close"].iloc[-(days + 1)])


def main() -> None:
    st.set_page_config(page_title="Market Dashboard", layout="wide")
    config = load_config()
    init_db()

    provider = get_provider(config)

    st.title("Market Dashboard")

    st.sidebar.header("Filters")
    asset_class = st.sidebar.selectbox(
        "Asset class",
        list(config["assets"].keys()),
    )

    asset_names = list(config["assets"][asset_class].keys())
    asset_name = st.sidebar.selectbox("Asset", asset_names)

    period = st.sidebar.selectbox("Period", ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "MAX"])
    interval = st.sidebar.selectbox("Interval", ["1d", "1h", "1m", "5m"])

    if st.sidebar.button("Update data now"):
        st.cache_data.clear()

    if st_autorefresh:
        if st.sidebar.checkbox("Auto refresh", value=False):
            st_autorefresh(interval=config["data"]["refresh_interval_seconds"] * 1000, key="auto_refresh")

    if st.sidebar.button("Test email alert"):
        try:
            test_email()
            st.sidebar.success("Test email sent")
        except Exception as exc:  # noqa: BLE001
            st.sidebar.error(f"Email failed: {exc}")

    asset = {"name": asset_name, **config["assets"][asset_class][asset_name]}
    symbol = asset.get("yahoo_symbol") or asset.get("symbol")

    asset_id = upsert_asset(
        name=asset_name,
        asset_class=asset_class,
        symbol=symbol,
        provider=config["data"]["default_provider"],
        currency=asset.get("currency", "USD"),
    )

    start_date, end_date = _period_to_dates(period)
    rows = provider.get_historical_data(asset, start_date, end_date, interval)
    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

    if df.empty:
        st.warning("No data available for this asset and interval.")
        return

    df["ma20"] = moving_average(df["close"], 20)
    df["ma50"] = moving_average(df["close"], 50)
    df["ma200"] = moving_average(df["close"], 200)
    df["rsi"] = rsi(df["close"], 14)
    bb = bollinger_bands(df["close"], 20, 2)
    df["bb_upper"] = bb["upper"]
    df["bb_lower"] = bb["lower"]
    df["returns"] = daily_returns(df["close"])
    df["vol_20d"] = realized_volatility(df["returns"].fillna(0.0), 20)
    df["drawdown"] = drawdown(df["close"])
    df["trend"] = trend_classification(df["close"], df["ma50"], df["ma200"])

    latest = provider.get_latest_price(asset)
    if latest:
        upsert_latest_price(
            asset_id=asset_id,
            timestamp=latest["timestamp"],
            last_price=safe_float(latest.get("last_price")),
            bid=latest.get("bid"),
            ask=latest.get("ask"),
            volume=latest.get("volume"),
            provider=latest.get("provider", "yfinance"),
            latency_seconds=latest.get("latency_seconds"),
        )

    st.subheader("Summary")
    change_1d = _calc_change(df, 1)
    change_5d = _calc_change(df, 5)
    change_1m = _calc_change(df, 22)
    ytd_change = _calc_change(df, min(252, len(df) - 1))

    st.write(
        {
            "last_price": df["close"].iloc[-1],
            "daily_change_pct": change_1d,
            "5d_change_pct": change_5d,
            "1m_change_pct": change_1m,
            "ytd_change_pct": ytd_change,
            "rsi": float(df["rsi"].iloc[-1]) if not df["rsi"].isna().all() else None,
            "trend": df["trend"].iloc[-1],
            "provider": config["data"]["default_provider"],
            "last_update": latest.get("timestamp") if latest else None,
        }
    )

    st.subheader("Class overview")
    class_assets = []
    for name, meta in config["assets"][asset_class].items():
        class_assets.append({"name": name, **meta})

    summary_df = _fetch_class_summary(class_assets, provider)
    st.dataframe(summary_df, use_container_width=True)

    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["close"], name="Close"))
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["ma20"], name="MA20"))
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["ma50"], name="MA50"))
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["ma200"], name="MA200"))
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_upper"], name="BB Upper"))
    fig_price.add_trace(go.Scatter(x=df["timestamp"], y=df["bb_lower"], name="BB Lower"))
    fig_price.update_layout(height=450, title="Price and Moving Averages")
    st.plotly_chart(fig_price, use_container_width=True)

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df["timestamp"], y=df["rsi"], name="RSI"))
    fig_rsi.update_layout(height=250, title="RSI")
    st.plotly_chart(fig_rsi, use_container_width=True)

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=df["timestamp"], y=df["drawdown"], name="Drawdown"))
    fig_dd.update_layout(height=250, title="Drawdown")
    st.plotly_chart(fig_dd, use_container_width=True)

    fig_ret = go.Figure()
    fig_ret.add_trace(go.Bar(x=df["timestamp"], y=df["returns"], name="Daily returns"))
    fig_ret.update_layout(height=250, title="Daily Returns (%)")
    st.plotly_chart(fig_ret, use_container_width=True)

    status = provider.get_provider_status()
    st.subheader("Provider status")
    st.json(
        {
            **status,
            "latency_seconds": provider.get_latency(),
            "realtime_badge": "real-time" if provider.is_realtime() else "delayed",
            "mode": status.get("mode"),
        }
    )

    signals = {
        "rsi_overbought": df["rsi"].iloc[-1] > 70,
        "rsi_oversold": df["rsi"].iloc[-1] < 30,
    }
    trigger_alerts(asset_id, asset_name, df["close"].iloc[-1], signals, config)


if __name__ == "__main__":
    main()
