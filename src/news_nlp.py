from __future__ import annotations

from typing import Any, Dict, List

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

try:
    from textblob import TextBlob
except Exception:  # noqa: BLE001
    TextBlob = None


_analyzer = SentimentIntensityAnalyzer()


IMPORTANT_KEYWORDS = {
    "surge",
    "drop",
    "supply shock",
    "inventory build",
    "inventory draw",
    "rate cut",
    "rate hike",
    "inflation",
    "geopolitical risk",
    "opec cut",
    "sanctions",
    "war",
    "recession",
    "china demand",
    "central bank",
    "fed",
    "dollar",
    "yields",
}


def sentiment_score(text: str) -> float:
    if not text:
        return 0.0
    score = _analyzer.polarity_scores(text)
    vader_score = score.get("compound", 0.0) * 100.0
    if TextBlob is None:
        return vader_score
    try:
        tb_score = TextBlob(text).sentiment.polarity * 100.0
        return (vader_score * 0.7) + (tb_score * 0.3)
    except Exception:  # noqa: BLE001
        return vader_score


def classify_sentiment(score: float) -> str:
    if score > 15:
        return "bullish"
    if score < -15:
        return "bearish"
    return "neutral"


def keyword_importance(text: str) -> float:
    text_lower = text.lower()
    hits = sum(1 for kw in IMPORTANT_KEYWORDS if kw in text_lower)
    return min(100.0, hits * 10.0)


def detect_events(text: str) -> List[str]:
    text_lower = text.lower()
    return [kw for kw in IMPORTANT_KEYWORDS if kw in text_lower]


def summarize_text(text: str, max_sentences: int = 2) -> str:
    if not text:
        return ""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return ". ".join(sentences[:max_sentences]) + ("." if sentences else "")


def analyze_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('raw_description', '')}"
        score = sentiment_score(text)
        events = detect_events(text)
        summary = summarize_text(article.get("raw_description", ""))
        enriched.append(
            {
                **article,
                "sentiment_score": score,
                "sentiment": classify_sentiment(score),
                "importance_score": keyword_importance(text),
                "impact_score": abs(score) * 0.6 + keyword_importance(text) * 0.3 + len(events) * 2.0,
                "content_summary": summary,
                "events": events,
            }
        )
    return enriched
