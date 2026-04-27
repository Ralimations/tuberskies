from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import render_editorial_list, render_panel_header, render_section_header
from youtube_cache import cached_video_performance
from youtube_client import (
    get_owned_video_metadata,
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
            ("Lowest first", "Metadata actions prioritize weaker uploads before healthy ones."),
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
            response = st.write_stream(stream_aria_response(prompt, st.session_state.vault_settings.get("ollama_model", "gemma")))
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


def render_creator_actions() -> None:
    render_section_header("Channel Ops", "Creator Actions", "Draft, review, and publish YouTube metadata with channel-safe guardrails.")
    _render_safety_note()

    video_df, video_message = cached_video_performance(st.session_state.vault_settings)
    if video_message:
        st.caption(video_message)

    _render_metadata_actions(video_df)
