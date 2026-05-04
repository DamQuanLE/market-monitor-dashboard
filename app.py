import streamlit as st

from src.database import init_db
from src.utils import ensure_dirs, load_config, setup_logging


def main() -> None:
    ensure_dirs()
    setup_logging()
    config = load_config()
    init_db()

    st.set_page_config(
        page_title="Market Monitor Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
    )

    st.title("Market Monitor Dashboard")
    st.caption("Local, single-app, multi-page Streamlit market monitor.")

    st.markdown(
        """
        Use the sidebar to navigate between pages:
        - Market Dashboard
        - News & AI Analysis
        - Prediction Signals
        - Alerts History
        - Settings
        """
    )

    st.subheader("Config summary")
    st.json(
        {
            "default_provider": config["data"]["default_provider"],
            "refresh_interval_seconds": config["data"]["refresh_interval_seconds"],
            "news_enabled": config["news"]["enabled"],
            "llm_enabled": config["llm"]["enabled"],
            "alerts_enabled": config["alerts"]["enabled"],
        }
    )


if __name__ == "__main__":
    main()
