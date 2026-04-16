from __future__ import annotations

import textwrap
from typing import Iterable

import ollama
import pandas as pd
import plotly.express as px
import streamlit as st

from mock_data import generate_analytics_data, summarize_channel
from storage import STAGES, load_calendar, load_vault_settings, save_calendar, save_vault_settings


st.set_page_config(layout="wide", page_title="YT Coach")


def initialize_state() -> None:
    if "analytics_df" not in st.session_state:
        st.session_state.analytics_df = generate_analytics_data()
    if "calendar_df" not in st.session_state:
        st.session_state.calendar_df = load_calendar()
    if "vault_settings" not in st.session_state:
        st.session_state.vault_settings = load_vault_settings()


def stream_ollama_response(prompt: str, model: str) -> Iterable[str]:
    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert YouTube strategist focused on clear, actionable guidance.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as error:  # pragma: no cover - UI fallback
        yield f"Local Ollama request failed: {error}"


def build_metric_row(df: pd.DataFrame) -> None:
    snapshot = summarize_channel(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Views (30d)", f"{snapshot.views:,}")
    col2.metric("Subscribers (30d)", f"{snapshot.subscribers:,}")
    col3.metric("Watch Time Hours (30d)", f"{snapshot.watch_time_hours:,}")


def build_analytics_chart(df: pd.DataFrame, metric_name: str) -> None:
    labels = {
        "ctr": "CTR (%)",
        "retention": "Retention (%)",
        "views": "Views",
    }
    chart = px.line(
        df,
        x="date",
        y=metric_name,
        markers=True,
        title=f"{labels[metric_name]} Over Time",
        template="plotly_white",
    )
    chart.update_layout(height=360, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(chart, use_container_width=True)


def render_command_center() -> None:
    st.subheader("Command Center")
    st.caption("Offline mock analytics with AI-ready chart context.")
    analytics_df = st.session_state.analytics_df
    build_metric_row(analytics_df)

    selected_metric = st.radio(
        "Chart focus",
        options=["ctr", "retention", "views"],
        format_func=lambda value: value.upper() if value == "ctr" else value.title(),
        horizontal=True,
    )

    left, right = st.columns([1.5, 1])
    with left:
        build_analytics_chart(analytics_df, selected_metric)
    with right:
        st.markdown("### Coaching Context")
        st.dataframe(analytics_df.tail(10), use_container_width=True, hide_index=True)

        if st.button("Analyze with Coach", key="command_center_coach"):
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            sample = analytics_df[["date", selected_metric]].tail(14).to_csv(index=False)
            prompt = textwrap.dedent(
                f"""
                Review this YouTube performance trend and explain what may be happening.
                Focus on practical actions a creator can take this week.

                Metric: {selected_metric}
                Data:
                {sample}
                """
            ).strip()
            with st.chat_message("assistant"):
                st.write_stream(stream_ollama_response(prompt, model))


def render_niche_lab() -> None:
    st.subheader("Niche Lab")
    st.caption("Brainstorm hooks, titles, and metadata with your local model.")
    topic = st.text_area(
        "Video topic or niche dump",
        placeholder="Example: cozy indie game reviews for burned-out adults",
        height=140,
    )

    col1, col2 = st.columns(2)
    working_title = col1.text_input("Working title", placeholder="Why Small Channels Lose CTR")
    model = col2.text_input(
        "Local Ollama model",
        value=st.session_state.vault_settings.get("ollama_model", "gemma"),
    )

    if st.button("Ask Coach", type="primary"):
        prompt = f"You are an expert YouTube strategist. Give me 5 viral video titles for the topic: {topic}"
        with st.chat_message("assistant"):
            st.write_stream(stream_ollama_response(prompt, model))

    if st.button("Generate Description + Tags"):
        prompt = textwrap.dedent(
            f"""
            Create a YouTube-optimized description and a comma-separated list of SEO tags.
            Topic context: {topic}
            Working title: {working_title}
            Keep the output skimmable.
            """
        ).strip()
        with st.chat_message("assistant"):
            st.write_stream(stream_ollama_response(prompt, model))


def render_content_calendar() -> None:
    st.subheader("Content Calendar")
    st.caption("Persistent local production board powered by `st.data_editor`.")

    edited_df = st.data_editor(
        st.session_state.calendar_df,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title", required=True, width="medium"),
            "stage": st.column_config.SelectboxColumn("Stage", options=STAGES, required=True),
            "target_upload_date": st.column_config.DateColumn("Target Upload Date", format="YYYY-MM-DD"),
            "notes": st.column_config.TextColumn("Notes", width="large"),
        },
        key="content_calendar_editor",
    )

    stage_counts = edited_df["stage"].fillna("Idea").value_counts().reindex(STAGES, fill_value=0)
    stage_chart = px.bar(
        x=stage_counts.index,
        y=stage_counts.values,
        labels={"x": "Pipeline Stage", "y": "Projects"},
        title="Pipeline Load",
        template="plotly_white",
    )
    st.plotly_chart(stage_chart, use_container_width=True)

    if st.button("Save Calendar"):
        normalized = edited_df.copy()
        normalized["stage"] = normalized["stage"].replace("", "Idea").fillna("Idea")
        st.session_state.calendar_df = normalized
        save_calendar(normalized)
        st.success("Content calendar saved locally.")


def render_vault() -> None:
    st.subheader("The Vault")
    st.caption("Local defaults and credentials storage for this machine only.")
    vault = st.session_state.vault_settings

    default_description = st.text_area(
        "Default Description",
        value=vault.get("default_description", ""),
        height=180,
        placeholder="Standard affiliate links, gear list, and socials...",
    )
    youtube_api_key = st.text_input(
        "YouTube API Key",
        value=vault.get("youtube_api_key", ""),
        type="password",
    )
    youtube_client_id = st.text_input(
        "YouTube Client ID",
        value=vault.get("youtube_client_id", ""),
        type="password",
    )
    youtube_client_secret = st.text_input(
        "YouTube Client Secret",
        value=vault.get("youtube_client_secret", ""),
        type="password",
    )
    ollama_model = st.selectbox(
        "Local LLM Model",
        options=["gemma", "gemma:7b", "llama3:8b"],
        index=["gemma", "gemma:7b", "llama3:8b"].index(vault.get("ollama_model", "gemma"))
        if vault.get("ollama_model", "gemma") in ["gemma", "gemma:7b", "llama3:8b"]
        else 0,
    )

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


def main() -> None:
    initialize_state()
    st.title("Local YT-Coach")
    st.caption("Private, offline-first YouTube dashboard and coaching workspace.")

    command_center, niche_lab, content_calendar, vault = st.tabs(
        ["Command Center", "Niche Lab", "Content Calendar", "The Vault"]
    )

    with command_center:
        render_command_center()
    with niche_lab:
        render_niche_lab()
    with content_calendar:
        render_content_calendar()
    with vault:
        render_vault()


if __name__ == "__main__":
    main()
