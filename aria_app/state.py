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
    if "calendar_coach_context" not in st.session_state:
        st.session_state.calendar_coach_context = "No repertoire coaching run yet."
    if "transcription_data" not in st.session_state:
        st.session_state.transcription_data = None
    if "shorts_segments" not in st.session_state:
        st.session_state.shorts_segments = []
    if "shorts_main_video_path" not in st.session_state:
        st.session_state.shorts_main_video_path = ""
    if "shorts_broll_video_path" not in st.session_state:
        st.session_state.shorts_broll_video_path = ""
    if "shorts_outputs" not in st.session_state:
        st.session_state.shorts_outputs = []
    if "shorts_analysis_error" not in st.session_state:
        st.session_state.shorts_analysis_error = ""
    if "youtube_auth_notice" not in st.session_state:
        st.session_state.youtube_auth_notice = ""
    if "coach_response_style" not in st.session_state:
        st.session_state.coach_response_style = "Concise"
    if "upload_takeaways" not in st.session_state:
        st.session_state.upload_takeaways = {}
