from __future__ import annotations

import streamlit as st

from storage import load_calendar, load_pattern_memory, load_vault_settings


def initialize_state() -> None:
    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "Command Center"
    if "analytics_source" not in st.session_state:
        st.session_state.analytics_source = "Live YouTube"
    if "calendar_df" not in st.session_state:
        st.session_state.calendar_df = load_calendar()
    if "vault_settings" not in st.session_state:
        st.session_state.vault_settings = load_vault_settings()
    if "pattern_memory" not in st.session_state:
        st.session_state.pattern_memory = load_pattern_memory()
    if "niche_output" not in st.session_state:
        st.session_state.niche_output = ""
    if "niche_last_action" not in st.session_state:
        st.session_state.niche_last_action = "No generation yet."
    if "calendar_coach_output" not in st.session_state:
        st.session_state.calendar_coach_output = ""
    if "youtube_auth_notice" not in st.session_state:
        st.session_state.youtube_auth_notice = ""
    if "coach_response_style" not in st.session_state:
        st.session_state.coach_response_style = "Concise"
    if "upload_takeaways" not in st.session_state:
        st.session_state.upload_takeaways = {}
    if "aria_analytics_chat" not in st.session_state:
        st.session_state.aria_analytics_chat = []
    if "command_center_section" not in st.session_state:
        st.session_state.command_center_section = "Dashboard"
    if "upload_lab_section" not in st.session_state:
        st.session_state.upload_lab_section = "Summary"
    if "momentum_workspace_section" not in st.session_state:
        st.session_state.momentum_workspace_section = "Snapshot"
    if "creator_metadata_status" not in st.session_state:
        st.session_state.creator_metadata_status = ""
    if "creator_metadata_title" not in st.session_state:
        st.session_state.creator_metadata_title = ""
    if "creator_metadata_description" not in st.session_state:
        st.session_state.creator_metadata_description = ""
    if "creator_metadata_tags" not in st.session_state:
        st.session_state.creator_metadata_tags = ""
    if "creator_metadata_ai_draft" not in st.session_state:
        st.session_state.creator_metadata_ai_draft = ""
    if "creator_comment_rows" not in st.session_state:
        st.session_state.creator_comment_rows = []
    if "creator_comment_status" not in st.session_state:
        st.session_state.creator_comment_status = ""
    if "creator_reply_draft" not in st.session_state:
        st.session_state.creator_reply_draft = ""
