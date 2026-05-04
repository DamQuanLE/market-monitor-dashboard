from __future__ import annotations

import numpy as np
import pandas as pd


def moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()


def exponential_moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    ma = moving_average(series, window)
    std = series.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return pd.DataFrame({"ma": ma, "upper": upper, "lower": lower})


def realized_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window=window).std() * np.sqrt(252)


def daily_returns(series: pd.Series) -> pd.Series:
    return series.pct_change() * 100.0


def cumulative_returns(series: pd.Series) -> pd.Series:
    return (1 + series.pct_change()).cumprod() - 1


def drawdown(series: pd.Series) -> pd.Series:
    cumulative = series / series.iloc[0]
    peak = cumulative.cummax()
    return (cumulative - peak) / peak


def breakout_20d(series: pd.Series) -> pd.Series:
    high_20 = series.rolling(window=20).max()
    return series > high_20.shift(1)


def breakdown_20d(series: pd.Series) -> pd.Series:
    low_20 = series.rolling(window=20).min()
    return series < low_20.shift(1)


def moving_average_crossover(fast: pd.Series, slow: pd.Series) -> pd.Series:
    return (fast > slow) & (fast.shift(1) <= slow.shift(1))


def trend_classification(series: pd.Series, ma_fast: pd.Series, ma_slow: pd.Series) -> pd.Series:
    trend = pd.Series(index=series.index, dtype="object")
    trend[(ma_fast > ma_slow) & (series > ma_fast)] = "bullish"
    trend[(ma_fast < ma_slow) & (series < ma_fast)] = "bearish"
    trend.fillna("neutral", inplace=True)
    return trend


def zscore_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    vol = returns.rolling(window=window).std()
    return (vol - vol.rolling(window=window).mean()) / vol.rolling(window=window).std()
