from __future__ import annotations

from typing import Any, Dict


def compute_final_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    return (
        scores.get("technical_score", 0.0) * weights.get("technical_score", 0.0)
        + scores.get("news_sentiment_score", 0.0) * weights.get("news_sentiment_score", 0.0)
        + scores.get("momentum_score", 0.0) * weights.get("momentum_score", 0.0)
        + scores.get("volatility_score", 0.0) * weights.get("volatility_score", 0.0)
        + scores.get("macro_score", 0.0) * weights.get("macro_score", 0.0)
    )


def label_signal(final_score: float) -> str:
    if final_score < -60:
        return "strong_bearish"
    if final_score < -25:
        return "bearish"
    if final_score <= 25:
        return "neutral"
    if final_score <= 60:
        return "bullish"
    return "strong_bullish"


def confidence_from_scores(scores: Dict[str, float]) -> float:
    values = [abs(v) for v in scores.values()]
    if not values:
        return 0.0
    return min(100.0, sum(values) / len(values))


def build_signal(scores: Dict[str, float], weights: Dict[str, float]) -> Dict[str, Any]:
    final_score = compute_final_score(scores, weights)
    return {
        **scores,
        "final_score": final_score,
        "signal_label": label_signal(final_score),
        "confidence": confidence_from_scores(scores),
    }
