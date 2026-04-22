from __future__ import annotations

import streamlit as st

from aria_app.ui import render_editorial_list, render_panel_header, render_section_header
from storage import load_vault_settings, save_vault_settings
from youtube_client import authorize_youtube_analytics, clear_youtube_token, get_connection_status, has_saved_token


def render_vault() -> None:
    render_section_header("Infrastructure", "The Vault", "Store defaults, model preferences, and future API credentials locally so the studio stays private, reusable, and aligned with Ralskies and A.R.I.A.")
    vault = st.session_state.vault_settings
    connection = get_connection_status(vault)
    token_ready = has_saved_token()

    left, right = st.columns([1.35, 0.85])
    with left:
        render_panel_header("Local Defaults", "Keep reusable metadata and model settings here so each new upload starts from a consistent base.")
        if connection.connected:
            st.success(connection.message)
        else:
            st.info(connection.message)
        default_description = st.text_area("Default Description", value=vault.get("default_description", ""), height=220, placeholder="Standard links, music platform URLs, Discord, and gear list...")
        ollama_model = st.selectbox(
            "Local LLM Model",
            options=["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"],
            index=["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"].index(vault.get("ollama_model", "gemma")) if vault.get("ollama_model", "gemma") in ["gemma", "gemma:7b", "llama3:8b", "gemma4:e2b"] else 0,
        )
        render_editorial_list(
            "YouTube Auth State",
            [
                ("API Key", "Present" if vault.get("youtube_api_key", "").strip() else "Missing"),
                ("OAuth Client", "Present" if vault.get("youtube_client_id", "").strip() and vault.get("youtube_client_secret", "").strip() else "Missing"),
                ("Saved Token", "Present" if token_ready else "Missing"),
            ],
        )
    with right:
        render_panel_header("API & Runtime", "Credentials can stay empty until you switch on live YouTube data. The app remains fully local without them.")
        youtube_api_key = st.text_input("YouTube API Key", value=vault.get("youtube_api_key", ""), type="password", placeholder="Leave blank for now")
        youtube_client_id = st.text_input("YouTube Client ID", value=vault.get("youtube_client_id", ""), type="password", placeholder="Leave blank for now")
        youtube_client_secret = st.text_input("YouTube Client Secret", value=vault.get("youtube_client_secret", ""), type="password", placeholder="Leave blank for now")
        render_editorial_list("Setup Notes", [("Privacy", "Local-first by default"), ("Live Data", "Now supports local OAuth and YouTube Analytics pulls"), ("Model Runtime", "Depends on your local Ollama install")])
        auth_col1, auth_col2 = st.columns(2)
        if auth_col1.button("Authorize YouTube", use_container_width=True):
            try:
                st.session_state.youtube_auth_notice = authorize_youtube_analytics(vault)
            except Exception as error:
                st.session_state.youtube_auth_notice = f"YouTube authorization failed: {error}"
        if auth_col2.button("Clear Local Token", use_container_width=True):
            clear_youtube_token()
            st.session_state.youtube_auth_notice = "The saved local YouTube token was removed."
        if st.session_state.youtube_auth_notice:
            st.info(st.session_state.youtube_auth_notice)
    if st.button("Save Vault Settings"):
        updated = {
            "DEFAULT_DESCRIPTION": default_description,
            "YOUTUBE_API_KEY": youtube_api_key,
            "YOUTUBE_CLIENT_ID": youtube_client_id,
            "YOUTUBE_CLIENT_SECRET": youtube_client_secret,
            "OLLAMA_MODEL": ollama_model,
        }
        save_vault_settings(updated)
        st.session_state.vault_settings = load_vault_settings()
        st.success("Vault settings saved to your local .env file.")
