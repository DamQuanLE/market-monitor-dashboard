from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests

from .utils import get_env

logger = logging.getLogger(__name__)


def fetch_news_for_asset(asset_name: str, keywords: List[str], language: str = "en") -> List[Dict[str, Any]]:
    api_key = get_env("NEWS_API_KEY")
    if not api_key:
        logger.warning("Missing NEWS_API_KEY")
        return []

    query = " OR ".join(keywords) if keywords else asset_name
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": 20,
        "sortBy": "publishedAt",
        "apiKey": api_key,
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for item in data.get("articles", []):
        articles.append(
            {
                "title": item.get("title"),
                "source": item.get("source", {}).get("name"),
                "url": item.get("url"),
                "published_at": item.get("publishedAt"),
                "raw_description": item.get("description") or "",
                "content_summary": item.get("content") or "",
            }
        )
    return articles
