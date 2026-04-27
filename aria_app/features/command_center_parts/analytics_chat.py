from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import render_panel_header


SUGGESTED_ANALYTICS_PROMPTS = [
    "What should I do next today?",
    "Which upload pattern should I repeat?",
    "What is the biggest risk in my analytics?",
    "What should I turn into Shorts?",
]


EMPTY_ASSISTANT_RESPONSE = "I could not produce a response from the local model. Check Ollama, then try again."


def _frame_preview(frame: pd.DataFrame | None, columns: list[str], rows: int = 8) -> str:
    if frame is None or frame.empty:
        return "No rows available."
    available_columns = [column for column in columns if column in frame.columns]
    if not available_columns:
        return "No matching columns available."
    return frame[available_columns].head(rows).to_csv(index=False)


def build_analytics_chat_context(
    analytics_df: pd.DataFrame,
    video_df: pd.DataFrame | None,
    calendar_df: pd.DataFrame,
    today_payload: dict[str, str],
    upload_takeaways: dict[str, object],
    pattern_snapshot: dict[str, object] | None,
) -> str:
    last_30 = analytics_df.tail(30) if analytics_df is not None else pd.DataFrame()
    last_7 = analytics_df.tail(7) if analytics_df is not None else pd.DataFrame()
    views_30 = int(last_30["views"].fillna(0).sum()) if not last_30.empty and "views" in last_30 else 0
    retention_7 = float(last_7["retention"].fillna(0).mean()) if not last_7.empty and "retention" in last_7 else 0
    watch_hours_30 = float(last_30["watch_time_hours"].fillna(0).sum()) if not last_30.empty and "watch_time_hours" in last_30 else 0

    best = upload_takeaways.get("best") if upload_takeaways else None
    weak = upload_takeaways.get("weak") if upload_takeaways else None
    best_line = "No best upload loaded."
    weak_line = "No weak upload loaded."
    if best is not None:
        best_line = f"{best.get('title', 'Unknown')} | views {best.get('views', 'n/a')} | retention {best.get('retention', 'n/a')} | score {best.get('engagement_score', 'n/a')}"
    if weak is not None:
        weak_line = f"{weak.get('title', 'Unknown')} | views {weak.get('views', 'n/a')} | retention {weak.get('retention', 'n/a')} | score {weak.get('engagement_score', 'n/a')}"

    return textwrap.dedent(
        f"""
        Current Ralskies Analytics Context:
        - Last 30 days views: {views_30:,}
        - Last 30 days watch time hours: {watch_hours_30:.1f}
        - Last 7 days average retention: {retention_7:.2f}%
        - Today focus: {today_payload.get("focus_title", "unknown")}
        - Today risk: {today_payload.get("risk_title", "unknown")} | {today_payload.get("risk_reason", "")}
        - Today opportunity: {today_payload.get("opportunity_title", "unknown")} | {today_payload.get("opportunity_reason", "")}
        - Recommended move: {today_payload.get("today_action", "")}
        - Best upload: {best_line}
        - Weakest upload: {weak_line}
        - Pattern memory snapshot: {pattern_snapshot or {}}

        Recent daily analytics:
        {_frame_preview(analytics_df.tail(14) if analytics_df is not None else None, ["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"], rows=14)}

        Top upload rows:
        {_frame_preview(video_df, ["title", "views", "retention", "watch_time_hours", "subscribers_gained", "comment_count", "engagement_score"], rows=8)}

        Repertoire rows:
        {_frame_preview(calendar_df, ["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"], rows=10)}
        """
    ).strip()


def _build_chat_prompt(user_prompt: str, context: str) -> str:
    recent_messages = st.session_state.aria_analytics_chat[-8:]
    recent_chat = "\n".join(f"{item['role']}: {item['content']}" for item in recent_messages)
    return textwrap.dedent(
        f"""
        You are A.R.I.A. answering as if the creator is chatting directly with their analytics.
        Use the analytics context below. Be concrete, brief, and action-oriented.
        If data is demo, cached, missing, or uncertain, say so plainly.
        Prefer specific next moves over generic advice.

        Analytics context:
        {context}

        Recent chat:
        {recent_chat or "No prior chat in this session."}

        Creator question:
        {user_prompt}
        """
    ).strip()


def _normalize_chat_history() -> None:
    cleaned_messages: list[dict[str, str]] = []
    for message in st.session_state.aria_analytics_chat:
        role = message.get("role", "")
        content = str(message.get("content", "")).strip()
        if role == "assistant" and not content:
            content = EMPTY_ASSISTANT_RESPONSE
        if not role or not content:
            continue
        if role == "user":
            latest_user = next((item for item in reversed(cleaned_messages) if item["role"] == "user"), None)
            if latest_user and latest_user["content"] == content:
                continue
        cleaned_messages.append({"role": role, "content": content})
    st.session_state.aria_analytics_chat = cleaned_messages[-16:]


def _latest_user_prompt() -> str:
    return next(
        (
            message["content"]
            for message in reversed(st.session_state.aria_analytics_chat)
            if message.get("role") == "user"
        ),
        "",
    )


def render_analytics_chat(
    analytics_df: pd.DataFrame,
    video_df: pd.DataFrame | None,
    calendar_df: pd.DataFrame,
    today_payload: dict[str, str],
    upload_takeaways: dict[str, object],
    pattern_snapshot: dict[str, object] | None,
) -> None:
    render_panel_header("Ask A.R.I.A.", "Chat with your channel data, upload history, repertoire, and action feed context.")
    _normalize_chat_history()

    context = build_analytics_chat_context(
        analytics_df=analytics_df,
        video_df=video_df,
        calendar_df=calendar_df,
        today_payload=today_payload,
        upload_takeaways=upload_takeaways,
        pattern_snapshot=pattern_snapshot,
    )

    prompt_from_button = ""
    cols = st.columns([1, 1, 1, 1, 0.7])
    for col, prompt in zip(cols[:4], SUGGESTED_ANALYTICS_PROMPTS):
        if col.button(prompt, key=f"aria_suggested_{prompt}", use_container_width=True):
            prompt_from_button = prompt
    if cols[4].button("Clear Chat", key="clear_aria_analytics_chat", use_container_width=True):
        st.session_state.aria_analytics_chat = []
        st.rerun()

    if st.session_state.aria_analytics_chat:
        for message in st.session_state.aria_analytics_chat:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    else:
        with st.chat_message("assistant"):
            st.write("Ask me what to fix, repeat, post, package, or turn into Shorts. I am reading the current analytics context for this session.")

    typed_prompt = ""
    with st.form("aria_analytics_chat_form", clear_on_submit=True):
        input_col, submit_col = st.columns([6, 1])
        typed_prompt = input_col.text_input(
            "Ask A.R.I.A. about your analytics",
            placeholder="Ask A.R.I.A. about your analytics...",
            label_visibility="collapsed",
        )
        submitted = submit_col.form_submit_button("Ask", type="primary", use_container_width=True)

    user_prompt = (prompt_from_button or (typed_prompt if submitted else "")).strip()
    if not user_prompt:
        return
    if _latest_user_prompt() == user_prompt:
        return

    st.session_state.aria_analytics_chat.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    model = st.session_state.vault_settings.get("ollama_model", "gemma")
    with st.chat_message("assistant"):
        response = st.write_stream(stream_aria_response(_build_chat_prompt(user_prompt, context), model))
        if not response:
            st.write(EMPTY_ASSISTANT_RESPONSE)
    assistant_response = response or EMPTY_ASSISTANT_RESPONSE
    st.session_state.aria_analytics_chat.append({"role": "assistant", "content": assistant_response})

    if len(st.session_state.aria_analytics_chat) > 16:
        st.session_state.aria_analytics_chat = st.session_state.aria_analytics_chat[-16:]
