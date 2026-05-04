from __future__ import annotations

import streamlit as st

from src.ai_report import analyze_news_with_llm
from src.database import fetch_news_articles, init_db, insert_news_articles, upsert_asset
from src.news_fetcher import fetch_news_for_asset
from src.news_nlp import analyze_articles
from src.utils import load_config


def main() -> None:
    st.set_page_config(page_title="News & AI Analysis", layout="wide")
    config = load_config()
    init_db()

    st.title("News & AI Analysis")

    asset_class = st.sidebar.selectbox("Asset class", list(config["assets"].keys()))
    asset_names = list(config["assets"][asset_class].keys())
    asset_name = st.sidebar.selectbox("Asset", asset_names)

    asset = {"name": asset_name, **config["assets"][asset_class][asset_name]}
    symbol = asset.get("yahoo_symbol") or asset.get("symbol")

    asset_id = upsert_asset(
        name=asset_name,
        asset_class=asset_class,
        symbol=symbol,
        provider=config["data"]["default_provider"],
        currency=asset.get("currency", "USD"),
    )

    if st.button("Update news now"):
        keywords = config["news"]["keywords"].get(asset_name, [asset_name])
        articles = fetch_news_for_asset(asset_name, keywords, config["news"]["language"])
        for a in articles:
            a["asset_id"] = asset_id
        insert_news_articles(articles)
        st.success(f"Fetched {len(articles)} articles")

    if st.button("Run NLP analysis"):
        articles = [dict(row) for row in fetch_news_articles(asset_id=asset_id, limit=50)]
        enriched = analyze_articles(articles)
        insert_news_articles(enriched)
        st.success("NLP analysis complete")

    if st.button("Run AI analysis with OpenAI/Gemini"):
        articles = [dict(row) for row in fetch_news_articles(asset_id=asset_id, limit=20)]
        market_data = {
            "last_price": None,
            "change_1d": None,
            "change_5d": None,
            "volatility_20d": None,
            "rsi": None,
            "ma50_position": None,
            "ma200_position": None,
        }
        result = analyze_news_with_llm(asset_name, articles, market_data, config)
        st.json(result)

    if st.button("Send daily report by email"):
        st.info("Daily digest generation is available in src/scheduler.py")

    st.subheader("Latest news")
    rows = fetch_news_articles(asset_id=asset_id, limit=100)
    for row in rows:
        st.markdown(f"**{row['title']}**")
        st.caption(f"{row['source']} | {row['published_at']}")
        if row["url"]:
            st.markdown(f"[{row['url']}]({row['url']})")
        st.write(row["raw_description"])
        st.write(
            {
                "sentiment": row["sentiment"],
                "sentiment_score": row["sentiment_score"],
                "importance_score": row["importance_score"],
                "impact_score": row["impact_score"],
            }
        )
        st.divider()


if __name__ == "__main__":
    main()
