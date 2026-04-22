from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from aria_app.ai import stream_ollama_response
from aria_app.ui import render_editorial_list, render_panel_header, render_section_header
from youtube_cache import cached_video_performance
from youtube_client import (
    get_owned_video_metadata,
    list_recent_comment_threads,
    reply_to_comment,
    update_owned_video_metadata,
)


ACTION_LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "creator_action_log.jsonl"


def _log_action(action: str, payload: dict[str, object]) -> None:
    ACTION_LOG_PATH.parent.mkdir(exist_ok=True)
    row = {"created_at": datetime.now().isoformat(timespec="seconds"), "action": action, "payload": payload}
    with ACTION_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _split_tags(raw_tags: str) -> list[str]:
    cleaned = raw_tags.replace("\n", ",")
    return [tag.strip().strip("#") for tag in cleaned.split(",") if tag.strip().strip("#")]


def _video_options(video_df: pd.DataFrame | None) -> list[tuple[str, str]]:
    if video_df is None or video_df.empty:
        return []
    options: list[tuple[str, str]] = []
    for _, row in video_df.head(50).iterrows():
        video_id = str(row.get("video_id", "")).strip()
        title = str(row.get("title", "Untitled Video")).strip()
        if video_id:
            options.append((f"{title[:72]} | {video_id}", video_id))
    return options


def _render_safety_note() -> None:
    render_editorial_list(
        "Safety Guardrails",
        [
            ("No autopilot", "A.R.I.A. drafts only; you approve each publish."),
            ("No bulk replies", "Replies are sent one comment at a time."),
            ("No duplicate spam", "Already-replied threads are flagged before posting."),
            ("Official API", "Uses YouTube OAuth, not browser automation."),
        ],
    )


def _render_metadata_actions(video_df: pd.DataFrame | None) -> None:
    render_panel_header("Metadata Actions", "Safely update one video's title, description, and tags after reviewing the current YouTube metadata.")
    options = _video_options(video_df)
    if not options:
        st.info("Connect YouTube and load upload history before editing metadata.")
        return

    labels = [label for label, _ in options]
    selected_label = st.selectbox("Video to optimize", options=labels, key="creator_actions_video_select")
    selected_video_id = dict(options)[selected_label]

    load_col, draft_col = st.columns(2)
    if load_col.button("Load Current Metadata", key="load_current_metadata", use_container_width=True):
        metadata, message = get_owned_video_metadata(st.session_state.vault_settings, selected_video_id)
        st.session_state.creator_metadata_status = message
        if metadata:
            st.session_state.creator_metadata_video_id = selected_video_id
            st.session_state.creator_metadata_title = metadata["title"]
            st.session_state.creator_metadata_description = metadata["description"]
            st.session_state.creator_metadata_tags = ", ".join(metadata.get("tags", []))
            st.session_state.creator_metadata_category_id = metadata.get("category_id", "10")
            st.session_state.creator_metadata_thumbnail = metadata.get("thumbnail_url", "")

    if draft_col.button("Draft Tags + Description", key="draft_metadata_ai", use_container_width=True):
        prompt = textwrap.dedent(
            f"""
            Draft safer YouTube metadata improvements for this Ralskies video.
            Return a concise result with:
            1. A refined description opening
            2. A comma-separated tag list under 450 total characters
            3. One caution if the current title should not be changed

            Current video: {selected_label}
            Current local pattern memory: {st.session_state.get("pattern_memory", {}).get("latest", {})}
            """
        ).strip()
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, st.session_state.vault_settings.get("ollama_model", "gemma")))
        st.session_state.creator_metadata_ai_draft = response or ""

    if st.session_state.get("creator_metadata_status"):
        st.info(st.session_state.creator_metadata_status)

    thumbnail = st.session_state.get("creator_metadata_thumbnail", "")
    if thumbnail:
        st.image(thumbnail, width=220)

    title = st.text_input("Reviewed title", value=st.session_state.get("creator_metadata_title", ""), max_chars=100, key="creator_metadata_title_input")
    description = st.text_area("Reviewed description", value=st.session_state.get("creator_metadata_description", ""), height=220, key="creator_metadata_description_input")
    tags_raw = st.text_area("Reviewed tags, comma-separated", value=st.session_state.get("creator_metadata_tags", ""), height=100, key="creator_metadata_tags_input")

    if st.session_state.get("creator_metadata_ai_draft"):
        with st.expander("A.R.I.A. metadata draft"):
            st.write(st.session_state.creator_metadata_ai_draft)

    tag_count = len(_split_tags(tags_raw))
    tag_chars = sum(len(tag) for tag in _split_tags(tags_raw)) + max(tag_count - 1, 0)
    render_editorial_list(
        "Preflight",
        [
            ("Title Length", f"{len(title.strip())}/100"),
            ("Description Bytes", f"{len(description.encode('utf-8'))}/5000"),
            ("Tags", f"{tag_count} tag(s), about {tag_chars}/500 chars"),
            ("Video ID", selected_video_id),
        ],
    )

    reviewed = st.checkbox("I reviewed this metadata and want to publish it to YouTube.", key="metadata_publish_reviewed")
    if st.button("Publish Metadata Update", type="primary", key="publish_metadata_update", disabled=not reviewed):
        success, message = update_owned_video_metadata(
            st.session_state.vault_settings,
            selected_video_id,
            title,
            description,
            _split_tags(tags_raw),
        )
        if success:
            _log_action("metadata_update", {"video_id": selected_video_id, "title": title, "tag_count": tag_count})
            st.success(message)
        else:
            st.error(message)


def _render_comment_actions(video_df: pd.DataFrame | None) -> None:
    render_panel_header("Comment Reply Inbox", "Review recent comments, draft a human reply, and post one reply at a time.")
    options = [("All recent channel comments", "")]
    options.extend(_video_options(video_df))
    labels = [label for label, _ in options]
    selected_label = st.selectbox("Comment source", options=labels, key="comment_source_select")
    selected_video_id = dict(options)[selected_label]

    load_col, draft_col = st.columns(2)
    if load_col.button("Load Recent Comments", key="load_recent_comments", use_container_width=True):
        rows, message = list_recent_comment_threads(st.session_state.vault_settings, video_id=selected_video_id, max_results=20)
        st.session_state.creator_comment_rows = rows
        st.session_state.creator_comment_status = message

    if st.session_state.get("creator_comment_status"):
        st.info(st.session_state.creator_comment_status)

    rows = st.session_state.get("creator_comment_rows", [])
    if not rows:
        st.info("Load comments to begin.")
        return

    comment_labels = []
    for index, row in enumerate(rows):
        status = "replied" if row.get("already_replied") else "open"
        comment_labels.append(f"{index + 1}. {row.get('author', 'Unknown')} | {status} | {str(row.get('text', ''))[:80]}")
    selected_comment_label = st.selectbox("Comment to review", options=comment_labels, key="selected_comment_label")
    selected_index = comment_labels.index(selected_comment_label)
    selected = rows[selected_index]

    render_editorial_list(
        "Selected Comment",
        [
            ("Author", str(selected.get("author", "Unknown"))),
            ("Can Reply", "Yes" if selected.get("can_reply") else "No"),
            ("Already Replied", "Yes" if selected.get("already_replied") else "No"),
            ("Replies", str(selected.get("reply_count", 0))),
        ],
    )
    st.text_area("Comment text", value=str(selected.get("text", "")), height=120, disabled=True)

    if draft_col.button("Draft Safe Reply", key="draft_comment_reply", use_container_width=True):
        prompt = textwrap.dedent(
            f"""
            Draft one warm, natural YouTube reply from Ralskies.
            Keep it specific, non-spammy, and under 300 characters.
            Do not overpromise. Do not use repeated promotional language.

            Comment author: {selected.get("author", "Unknown")}
            Comment: {selected.get("text", "")}
            """
        ).strip()
        with st.chat_message("assistant"):
            response = st.write_stream(stream_ollama_response(prompt, st.session_state.vault_settings.get("ollama_model", "gemma")))
        st.session_state.creator_reply_draft = response or ""

    reply_text = st.text_area("Reviewed reply", value=st.session_state.get("creator_reply_draft", ""), height=120, key="creator_reply_text")
    reviewed = st.checkbox("I reviewed this reply and want to post it to YouTube.", key="comment_reply_reviewed")
    disabled = not reviewed or not selected.get("can_reply") or selected.get("already_replied")
    if st.button("Post One Reply", type="primary", key="post_one_reply", disabled=disabled):
        success, message = reply_to_comment(st.session_state.vault_settings, str(selected.get("comment_id", "")), reply_text)
        if success:
            _log_action("comment_reply", {"comment_id": selected.get("comment_id", ""), "video_id": selected.get("video_id", "")})
            st.success(message)
            st.session_state.creator_reply_draft = ""
        else:
            st.error(message)
    if selected.get("already_replied"):
        st.warning("This thread already has a channel reply loaded in the current API response. A.R.I.A. will not post another from this screen.")


def render_creator_actions() -> None:
    render_section_header("Channel Ops", "Creator Actions", "Draft, review, and publish YouTube metadata or comment replies with channel-safe guardrails.")
    _render_safety_note()

    video_df, video_message = cached_video_performance(st.session_state.vault_settings)
    if video_message:
        st.caption(video_message)

    active = st.radio("Action type", options=["Metadata", "Comments"], horizontal=True, label_visibility="collapsed")
    if active == "Metadata":
        _render_metadata_actions(video_df)
    else:
        _render_comment_actions(video_df)
