from __future__ import annotations

from typing import Any, Dict, List

from .llm_client import parse_json_response, run_llm
from .prompt_templates import NEWS_ANALYSIS_PROMPT


def analyze_news_with_llm(
    asset: str,
    articles: List[Dict[str, Any]],
    market_data: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    if not config["llm"]["enabled"]:
        return {"error": "llm_disabled"}

    articles_text = "\n".join(
        [f"- {a.get('title')} | {a.get('raw_description', '')}" for a in articles[:10]]
    )

    prompt = NEWS_ANALYSIS_PROMPT.format(
        asset=asset,
        last_price=market_data.get("last_price"),
        change_1d=market_data.get("change_1d"),
        change_5d=market_data.get("change_5d"),
        volatility_20d=market_data.get("volatility_20d"),
        rsi=market_data.get("rsi"),
        ma50_position=market_data.get("ma50_position"),
        ma200_position=market_data.get("ma200_position"),
        articles=articles_text,
    )

    raw = run_llm(prompt, config)
    return parse_json_response(raw)
