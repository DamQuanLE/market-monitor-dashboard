from __future__ import annotations

import streamlit as st

from src.database import fetch_alert_history, get_assets, init_db
from src.utils import load_config


def main() -> None:
    st.set_page_config(page_title="Alerts History", layout="wide")
    init_db()
    config = load_config()

    st.title("Alerts History")

    assets = get_assets()
    asset_map = {row["id"]: row["name"] for row in assets}
    asset_options = ["All"] + [row["name"] for row in assets]

    selected_asset = st.sidebar.selectbox("Asset", asset_options)
    selected_type = st.sidebar.selectbox(
        "Alert type",
        [
            "All",
            "price above",
            "price below",
            "daily change above",
            "daily change below",
            "RSI > 70",
            "RSI < 30",
            "moving average crossover",
            "breakout 20d",
            "breakdown 20d",
            "abnormal volatility",
            "important news detected",
            "AI sentiment shift",
            "strong bullish score",
            "strong bearish score",
        ],
    )

    rows = fetch_alert_history(limit=500)
    filtered = []
    for row in rows:
        asset_name = asset_map.get(row["asset_id"], "Unknown")
        if selected_asset != "All" and asset_name != selected_asset:
            continue
        if selected_type != "All" and row["alert_type"] != selected_type:
            continue
        filtered.append({**dict(row), "asset_name": asset_name})

    st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    main()
