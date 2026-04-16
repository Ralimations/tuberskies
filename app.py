from __future__ import annotations

import textwrap
from datetime import date, timedelta
from typing import Iterable

import ollama
import pandas as pd
import plotly.express as px
import streamlit as st

from mock_data import generate_analytics_data, summarize_channel
from storage import STAGES, load_calendar, load_vault_settings, save_calendar, save_vault_settings
from youtube_client import get_connection_status, load_live_analytics_placeholder


st.set_page_config(layout="wide", page_title="YT Coach")


def initialize_state() -> None:
    if "analytics_df" not in st.session_state:
        st.session_state.analytics_df = generate_analytics_data()
    if "analytics_source" not in st.session_state:
        st.session_state.analytics_source = "Mock Data"
    if "calendar_df" not in st.session_state:
        st.session_state.calendar_df = load_calendar()
    if "vault_settings" not in st.session_state:
        st.session_state.vault_settings = load_vault_settings()
    if "niche_output" not in st.session_state:
        st.session_state.niche_output = ""
    if "niche_last_action" not in st.session_state:
        st.session_state.niche_last_action = "No generation yet."


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


def build_health_snapshot(df: pd.DataFrame) -> None:
    latest = df.tail(7)
    previous = df.tail(14).head(7)
    if latest.empty or previous.empty:
        return

    ctr_delta = latest["ctr"].mean() - previous["ctr"].mean()
    retention_delta = latest["retention"].mean() - previous["retention"].mean()
    views_delta = latest["views"].sum() - previous["views"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("CTR vs Prev 7d", f"{latest['ctr'].mean():.2f}%", f"{ctr_delta:+.2f} pts")
    col2.metric(
        "Retention vs Prev 7d",
        f"{latest['retention'].mean():.2f}%",
        f"{retention_delta:+.2f} pts",
    )
    col3.metric("Views vs Prev 7d", f"{latest['views'].sum():,}", f"{views_delta:+,}")


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


def get_alert_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["ctr"] < 5.0) | (df["retention"] < 42.0)].sort_values("date", ascending=False)


def build_coach_prompt(topic: str, working_title: str, action: str) -> str:
    prompts = {
        "title_pack": f"""
        You are an expert YouTube strategist.
        Generate 5 viral video titles for the topic below.
        Include a one-line angle note under each title.

        Topic: {topic}
        Working title: {working_title}
        """,
        "description_tags": f"""
        Create a YouTube-optimized description and a comma-separated list of SEO tags.
        Keep the result clean and skimmable.

        Topic context: {topic}
        Working title: {working_title}
        """,
        "hook_pack": f"""
        You are an expert retention-focused YouTube strategist.
        Generate 10 opening hooks for this video idea.
        Make them sound natural, curiosity-driven, and high-retention.

        Topic: {topic}
        Working title: {working_title}
        """,
        "content_brief": f"""
        Build a practical YouTube content brief for this idea.
        Include target viewer, promise, thumbnail concept, outline, and call to action.

        Topic: {topic}
        Working title: {working_title}
        """,
    }
    return textwrap.dedent(prompts[action]).strip()


def normalize_calendar_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized["title"] = normalized["title"].fillna("").astype(str)
    normalized["stage"] = normalized["stage"].replace("", "Idea").fillna("Idea")
    normalized["notes"] = normalized["notes"].fillna("").astype(str)
    normalized["target_upload_date"] = pd.to_datetime(normalized["target_upload_date"], errors="coerce")
    return normalized


def render_command_center() -> None:
    st.subheader("Command Center")
    st.caption("Offline-first analytics with a live YouTube connection path ready when you want it.")

    source = st.segmented_control(
        "Data source",
        options=["Mock Data", "Live YouTube"],
        default=st.session_state.analytics_source,
        key="analytics_source_picker",
    )
    st.session_state.analytics_source = source

    live_df, live_message = load_live_analytics_placeholder(st.session_state.vault_settings)
    using_live = source == "Live YouTube" and live_df is not None
    analytics_df = live_df if using_live else st.session_state.analytics_df

    if source == "Live YouTube" and live_df is None:
        st.info(live_message)

    build_metric_row(analytics_df)
    build_health_snapshot(analytics_df)

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

        alerts = get_alert_rows(analytics_df).head(5)
        if alerts.empty:
            st.success("No major mock-data alerts right now.")
        else:
            st.warning("Potential weak spots detected in recent performance.")
            st.dataframe(
                alerts[["date", "views", "ctr", "retention"]],
                use_container_width=True,
                hide_index=True,
            )

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

    action_labels = {
        "title_pack": "Title Pack",
        "hook_pack": "Hook Pack",
        "description_tags": "Description + Tags",
        "content_brief": "Content Brief",
    }
    selected_action = st.selectbox(
        "Generation mode",
        options=list(action_labels.keys()),
        format_func=lambda value: action_labels[value],
    )

    col1, col2, col3 = st.columns([1, 1, 1.2])
    run_primary = col1.button("Ask Coach", type="primary")
    run_secondary = col2.button("Quick Hooks")
    clear_output = col3.button("Clear Output")

    if clear_output:
        st.session_state.niche_output = ""
        st.session_state.niche_last_action = "Output cleared."

    if run_primary:
        prompt = build_coach_prompt(topic, working_title, selected_action)
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, model))
        st.session_state.niche_output = response or ""
        st.session_state.niche_last_action = action_labels[selected_action]

    if run_secondary:
        prompt = build_coach_prompt(topic, working_title, "hook_pack")
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, model))
        st.session_state.niche_output = response or ""
        st.session_state.niche_last_action = "Hook Pack"

    st.markdown("### Workspace")
    result_col, notes_col = st.columns([1.5, 1])
    with result_col:
        st.text_area(
            "Last Coach Output",
            value=st.session_state.niche_output,
            height=280,
            placeholder="Generated ideas will appear here...",
        )
    with notes_col:
        st.markdown(f"**Last action:** {st.session_state.niche_last_action}")
        st.markdown("**Prompt tips**")
        st.caption(
            "The best results usually come from a clear topic, a rough audience, and one sharp promise."
        )
        st.markdown("**Suggested angles**")
        st.caption(
            "Try adding stakes, transformation, or a narrow viewer persona like beginners, freelancers, or new parents."
        )


def render_content_calendar() -> None:
    st.subheader("Content Calendar")
    st.caption("Persistent local production board powered by `st.data_editor`.")

    today = pd.Timestamp(date.today())
    default_due = today + pd.Timedelta(days=7)

    quick_add_col1, quick_add_col2, quick_add_col3, quick_add_col4 = st.columns([1.4, 1, 1, 0.9])
    quick_title = quick_add_col1.text_input("Quick add title", placeholder="New upload idea")
    quick_stage = quick_add_col2.selectbox("Quick stage", options=STAGES, index=0)
    quick_date = quick_add_col3.date_input("Target date", value=default_due.to_pydatetime())
    add_project = quick_add_col4.button("Add Project", use_container_width=True)

    if add_project and quick_title.strip():
        new_row = pd.DataFrame(
            [
                {
                    "title": quick_title.strip(),
                    "stage": quick_stage,
                    "target_upload_date": pd.Timestamp(quick_date),
                    "notes": "",
                }
            ]
        )
        st.session_state.calendar_df = pd.concat(
            [st.session_state.calendar_df, new_row], ignore_index=True
        )
        save_calendar(st.session_state.calendar_df)
        st.success("Project added to your local calendar.")

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
    edited_df = normalize_calendar_df(edited_df)

    stage_counts = edited_df["stage"].value_counts().reindex(STAGES, fill_value=0)
    due_soon = edited_df[
        edited_df["target_upload_date"].notna()
        & (edited_df["target_upload_date"] >= today)
        & (edited_df["target_upload_date"] <= today + pd.Timedelta(days=14))
    ].sort_values("target_upload_date")
    ready_count = int(stage_counts.get("Ready for Upload", 0))

    top_row1, top_row2, top_row3 = st.columns(3)
    top_row1.metric("Total Projects", f"{len(edited_df):,}")
    top_row2.metric("Ready to Upload", ready_count)
    top_row3.metric("Due in 14 Days", f"{len(due_soon):,}")

    left, right = st.columns([1.2, 1])
    with left:
        stage_chart = px.bar(
            x=stage_counts.index,
            y=stage_counts.values,
            labels={"x": "Pipeline Stage", "y": "Projects"},
            title="Pipeline Load",
            template="plotly_white",
        )
        st.plotly_chart(stage_chart, use_container_width=True)
    with right:
        st.markdown("### Upcoming Deadlines")
        if due_soon.empty:
            st.info("No projects due in the next 14 days.")
        else:
            st.dataframe(
                due_soon[["title", "stage", "target_upload_date"]],
                use_container_width=True,
                hide_index=True,
            )

    action_col1, action_col2 = st.columns([1, 1.5])
    if action_col1.button("Save Calendar"):
        st.session_state.calendar_df = edited_df
        save_calendar(edited_df)
        st.success("Content calendar saved locally.")
    if action_col2.button("Autosave Current Table"):
        st.session_state.calendar_df = edited_df
        save_calendar(edited_df)
        st.success("Current editor state saved.")


def render_vault() -> None:
    st.subheader("The Vault")
    st.caption("Local defaults and credentials storage for this machine only.")
    vault = st.session_state.vault_settings
    connection = get_connection_status(vault)

    if connection.connected:
        st.success(connection.message)
    else:
        st.info(connection.message)

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
        placeholder="Leave blank for now",
    )
    youtube_client_id = st.text_input(
        "YouTube Client ID",
        value=vault.get("youtube_client_id", ""),
        type="password",
        placeholder="Leave blank for now",
    )
    youtube_client_secret = st.text_input(
        "YouTube Client Secret",
        value=vault.get("youtube_client_secret", ""),
        type="password",
        placeholder="Leave blank for now",
    )
    ollama_model = st.selectbox(
        "Local LLM Model",
        options=["gemma", "gemma:7b", "llama3:8b"],
        index=["gemma", "gemma:7b", "llama3:8b"].index(vault.get("ollama_model", "gemma"))
        if vault.get("ollama_model", "gemma") in ["gemma", "gemma:7b", "llama3:8b"]
        else 0,
    )

    st.markdown("### Setup Notes")
    st.caption(
        "This app stays local-first. Leave API fields empty until you want to enable live YouTube data."
    )
    st.caption(
        "Ollama responses stream from your local machine, so generation speed depends on the model you have pulled."
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
