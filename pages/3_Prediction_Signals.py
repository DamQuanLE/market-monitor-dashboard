from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from src.data_providers.provider_factory import get_provider
from src.indicators import daily_returns, moving_average, realized_volatility, rsi
from src.prediction_model import build_signal
from src.utils import load_config


def _period_dates(days: int) -> tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return start.date().isoformat(), end.date().isoformat()


def _score_asset(asset: Dict[str, Any], provider, weights: Dict[str, float]) -> Dict[str, Any]:
    start, end = _period_dates(365)
    rows = provider.get_historical_data(asset, start, end, "1d")
    df = pd.DataFrame(rows)
    if df.empty:
        return {"asset": asset["name"], "final_score": 0.0, "signal_label": "neutral"}
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    df["ma20"] = moving_average(df["close"], 20)
    df["ma50"] = moving_average(df["close"], 50)
    df["rsi"] = rsi(df["close"], 14)
    df["returns"] = daily_returns(df["close"]) / 100.0
    df["vol_20d"] = realized_volatility(df["returns"].fillna(0.0), 20)

    technical_score = 0.0
    if df["rsi"].iloc[-1] > 70:
        technical_score -= 30
    elif df["rsi"].iloc[-1] < 30:
        technical_score += 30

    momentum_score = (df["close"].iloc[-1] / df["close"].iloc[-21] - 1) * 100
    volatility_score = -df["vol_20d"].iloc[-1] * 10 if pd.notna(df["vol_20d"].iloc[-1]) else 0.0

    scores = {
        "technical_score": float(technical_score),
        "news_sentiment_score": 0.0,
        "momentum_score": float(momentum_score),
        "volatility_score": float(volatility_score),
        "macro_score": 0.0,
    }
    signal = build_signal(scores, weights)
    return {"asset": asset["name"], **signal}


def main() -> None:
    st.set_page_config(page_title="Prediction Signals", layout="wide")
    config = load_config()
    provider = get_provider(config)

    st.title("Prediction Signals")
    st.caption("Scores are indicative and probabilistic, for monitoring only.")

    asset_class = st.sidebar.selectbox("Asset class", list(config["assets"].keys()))
    assets = [{"name": name, **meta} for name, meta in config["assets"][asset_class].items()]

    weights = config["prediction"]["weights"]

    rows = []
    for asset in assets:
        rows.append(_score_asset(asset, provider, weights))

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    top_bullish = df.sort_values("final_score", ascending=False).head(3)
    top_bearish = df.sort_values("final_score", ascending=True).head(3)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top bullish")
        st.dataframe(top_bullish, use_container_width=True)
    with col2:
        st.subheader("Top bearish")
        st.dataframe(top_bearish, use_container_width=True)


if __name__ == "__main__":
    main()
