from __future__ import annotations

import streamlit as st

from src.database import get_setting, init_db, set_setting
from src.utils import get_env, load_config


def main() -> None:
    st.set_page_config(page_title="Settings", layout="wide")
    config = load_config()
    init_db()

    st.title("Settings")

    provider_options = list(config["data"]["providers"].keys())
    current_provider = get_setting("default_provider") or config["data"]["default_provider"]
    selected_provider = st.selectbox("Default provider", provider_options, index=provider_options.index(current_provider))

    refresh_current = int(get_setting("refresh_interval_seconds") or config["data"]["refresh_interval_seconds"])
    refresh_interval = st.number_input("Refresh interval (seconds)", min_value=5, max_value=3600, value=refresh_current)

    alerts_enabled = st.checkbox("Alerts enabled", value=config["alerts"]["enabled"])
    email_enabled = st.checkbox("Email alerts enabled", value=config["alerts"]["email_enabled"])

    if st.button("Save settings"):
        set_setting("default_provider", selected_provider)
        set_setting("refresh_interval_seconds", str(int(refresh_interval)))
        set_setting("alerts_enabled", str(alerts_enabled))
        set_setting("email_enabled", str(email_enabled))
        st.success("Settings saved")

    st.subheader("API key status")
    st.write(
        {
            "OPENAI_API_KEY": bool(get_env("OPENAI_API_KEY")),
            "GEMINI_API_KEY": bool(get_env("GEMINI_API_KEY")),
            "NEWS_API_KEY": bool(get_env("NEWS_API_KEY")),
            "FRED_API_KEY": bool(get_env("FRED_API_KEY")),
        }
    )


if __name__ == "__main__":
    main()
