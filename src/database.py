import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from .utils import DB_PATH, now_utc


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                symbol TEXT,
                provider TEXT,
                currency TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                interval TEXT,
                provider TEXT
            );

            CREATE TABLE IF NOT EXISTS latest_prices (
                asset_id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                last_price REAL,
                bid REAL,
                ask REAL,
                volume REAL,
                provider TEXT,
                latency_seconds REAL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                threshold REAL,
                condition TEXT,
                enabled INTEGER DEFAULT 1,
                cooldown_hours INTEGER,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT,
                price REAL,
                triggered_at TEXT,
                email_sent INTEGER,
                cooldown_until TEXT
            );

            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                title TEXT,
                source TEXT,
                url TEXT,
                published_at TEXT,
                raw_description TEXT,
                content_summary TEXT,
                sentiment TEXT,
                sentiment_score REAL,
                importance_score REAL,
                impact_score REAL,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                analysis_date TEXT,
                sentiment_score REAL,
                bullish_score REAL,
                bearish_score REAL,
                uncertainty_score REAL,
                summary TEXT,
                bullish_factors TEXT,
                bearish_factors TEXT,
                risk_factors TEXT,
                llm_provider TEXT,
                model_used TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS prediction_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                timestamp TEXT,
                technical_score REAL,
                news_sentiment_score REAL,
                momentum_score REAL,
                volatility_score REAL,
                macro_score REAL,
                final_score REAL,
                signal_label TEXT,
                confidence REAL,
                explanation TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
            """
        )
        conn.commit()


def upsert_asset(name: str, asset_class: str, symbol: Optional[str], provider: str, currency: str) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id FROM assets WHERE name = ? AND asset_class = ?
            """,
            (name, asset_class),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE assets
                SET symbol = ?, provider = ?, currency = ?, is_active = 1
                WHERE id = ?
                """,
                (symbol, provider, currency, row["id"]),
            )
            conn.commit()
            return int(row["id"])

        cur.execute(
            """
            INSERT INTO assets (name, asset_class, symbol, provider, currency, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (name, asset_class, symbol, provider, currency, now_utc().isoformat()),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_assets() -> List[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM assets WHERE is_active = 1 ORDER BY asset_class, name")
        return cur.fetchall()


def upsert_latest_price(
    asset_id: int,
    timestamp: str,
    last_price: float,
    bid: float | None,
    ask: float | None,
    volume: float | None,
    provider: str,
    latency_seconds: float | None,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO latest_prices (asset_id, timestamp, last_price, bid, ask, volume, provider, latency_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                timestamp = excluded.timestamp,
                last_price = excluded.last_price,
                bid = excluded.bid,
                ask = excluded.ask,
                volume = excluded.volume,
                provider = excluded.provider,
                latency_seconds = excluded.latency_seconds
            """,
            (asset_id, timestamp, last_price, bid, ask, volume, provider, latency_seconds),
        )
        conn.commit()


def fetch_latest_price(asset_id: int) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM latest_prices WHERE asset_id = ?", (asset_id,))
        return cur.fetchone()


def insert_prices(
    asset_id: int,
    rows: List[Dict[str, Any]],
    interval: str,
    provider: str,
) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT INTO prices (asset_id, timestamp, open, high, low, close, volume, interval, provider)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    asset_id,
                    row["timestamp"],
                    row["open"],
                    row["high"],
                    row["low"],
                    row["close"],
                    row.get("volume"),
                    interval,
                    provider,
                )
                for row in rows
            ],
        )
        conn.commit()


def fetch_prices(asset_id: int, limit: int = 500) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM prices WHERE asset_id = ? ORDER BY timestamp DESC LIMIT ?
            """,
            (asset_id, limit),
        )
        return cur.fetchall()


def insert_news_articles(articles: List[Dict[str, Any]]) -> None:
    if not articles:
        return
    with get_connection() as conn:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT INTO news_articles
            (asset_id, title, source, url, published_at, raw_description, content_summary,
             sentiment, sentiment_score, importance_score, impact_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    a.get("asset_id"),
                    a.get("title"),
                    a.get("source"),
                    a.get("url"),
                    a.get("published_at"),
                    a.get("raw_description"),
                    a.get("content_summary"),
                    a.get("sentiment"),
                    a.get("sentiment_score"),
                    a.get("importance_score"),
                    a.get("impact_score"),
                    now_utc().isoformat(),
                )
                for a in articles
            ],
        )
        conn.commit()


def fetch_news_articles(asset_id: Optional[int] = None, limit: int = 200) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.cursor()
        if asset_id:
            cur.execute(
                """
                SELECT * FROM news_articles
                WHERE asset_id = ?
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (asset_id, limit),
            )
        else:
            cur.execute(
                """
                SELECT * FROM news_articles
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        return cur.fetchall()


def insert_alert_history(entry: Dict[str, Any]) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO alert_history
            (asset_id, alert_type, message, price, triggered_at, email_sent, cooldown_until)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.get("asset_id"),
                entry.get("alert_type"),
                entry.get("message"),
                entry.get("price"),
                entry.get("triggered_at"),
                1 if entry.get("email_sent") else 0,
                entry.get("cooldown_until"),
            ),
        )
        conn.commit()


def fetch_alert_history(limit: int = 200) -> List[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM alert_history ORDER BY triggered_at DESC LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now_utc().isoformat()),
        )
        conn.commit()


def get_setting(key: str) -> Optional[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None
