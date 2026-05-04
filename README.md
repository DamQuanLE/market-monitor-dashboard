# Market Monitor Dashboard

Local Streamlit multi-page dashboard for market monitoring across commodities, stocks, bonds/rates, macro and crypto. This app is designed for analysis and monitoring only. It does not provide direct financial advice and does not automate trading.

## Architecture (high level)
- Provider layer fetches market data (yfinance for MVP, optional real-time providers later).
- Live cache stores latest prices in memory.
- SQLite stores assets, prices, alerts, news, AI analysis and signals.
- Streamlit pages read from cache/DB and compute indicators on demand.

```
Provider API/WebSocket
        |
Live data manager
        |
In-memory latest cache
        |
Bar aggregator (1s/5s/1m)
        |
SQLite / Parquet
        |
Streamlit UI
```

## Install
Create a virtual environment and install dependencies.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Mac/Linux:
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Configuration
- Copy .env.example to .env and fill your API keys.
- Review config.yaml to enable providers and assets.

## Run
```bash
streamlit run app.py
```

## Add a new commodity
1. Open config.yaml.
2. Add a new entry under assets -> commodities.
3. Provide at least a yahoo_symbol and currency.
4. Restart the app.

Example:
```yaml
  commodities:
    Aluminum:
      type: "future"
      yahoo_symbol: "ALI=F"
      currency: "USD"
```

## Change provider
1. Open config.yaml.
2. Set data.default_provider to your provider key.
3. Enable the provider under data.providers.
4. Add required API keys to .env.

Example:
```yaml
data:
  default_provider: "fred"
  providers:
    fred:
      enabled: true
      api_key_env: "FRED_API_KEY"
```

## Configure email alerts
1. Add SMTP settings to .env.
2. Ensure alerts.enabled and alerts.email_enabled are true in config.yaml.
3. Use the "Test email" button in the Market Dashboard page.

## Notes on data sources
- yfinance is for low-frequency monitoring only.
- Some providers are delayed or daily only.
- Real-time streaming is optional and requires extra setup.

## Disclaimer
This application is for monitoring and analysis only. It does not provide financial advice, does not recommend trades, and does not execute orders.
