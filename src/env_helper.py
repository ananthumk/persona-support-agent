import os


def get_api_key() -> str:
    """
    Returns the Gemini API key, checking environment variables first
    (works locally via .env), then falling back to Streamlit secrets
    (works on Streamlit Community Cloud, where .env files don't exist).
    """
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key

    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""