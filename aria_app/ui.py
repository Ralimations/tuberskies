from __future__ import annotations

import streamlit as st

from .theme import APP_CSS
from .navigation import PAGE_LABELS
from youtube_client import get_live_channel_profile, has_saved_token


QUICK_JUMP_TARGETS = {
    "Today Desk": {
        "selected_view": "Command Center",
        "command_center_section": "Today Desk",
    },
    "Upload Radar": {
        "selected_view": "Command Center",
        "command_center_section": "Upload Lab",
        "upload_lab_section": "Radar",
    },
    "Pattern Memory": {
        "selected_view": "Command Center",
        "command_center_section": "Pattern Memory",
    },
    "Request Signals": {
        "selected_view": "Niche Lab",
        "niche_lab_section": "Request Signals",
    },
    "Repertoire Timeline": {
        "selected_view": "Repertoire",
        "repertoire_section": "Timeline",
    },
    "Shorts Cutting": {
        "selected_view": "Shorts Architect",
        "shorts_section": "Cutting Room",
    },
}

CONTEXTUAL_JUMP_GROUPS = {
    "Command Center": ["Today Desk", "Upload Radar", "Pattern Memory"],
    "Niche Lab": ["Request Signals"],
    "Repertoire": ["Repertoire Timeline"],
    "Shorts Architect": ["Shorts Cutting"],
    "The Vault": ["Pattern Memory", "Today Desk"],
}


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="appbar-shell">
            <div class="appbar-left">
                <div class="appbar-mark">RS</div>
                <div>
                    <div class="appbar-title">Ralskies Creator Studio</div>
                    <div class="appbar-copy">Dashboard, analytics, repertoire, and release decisions in one private workspace.</div>
                </div>
            </div>
            <div class="appbar-right">
                <div class="masthead-pill">Creator Dashboard</div>
                <div class="masthead-pill">Analytics</div>
                <div class="masthead-pill">A.R.I.A.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    with st.sidebar:
        channel_profile = None
        channel_message = ""
        if has_saved_token():
            channel_profile, channel_message = get_live_channel_profile(st.session_state.vault_settings)

        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-kicker">Ralskies Studio OS</div>
                <div class="sidebar-title">A.R.I.A.</div>
                <div class="sidebar-copy">
                    A quieter control room for planning releases, reading signals, and guiding the next upload.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if channel_profile:
            if channel_profile.get("thumbnail_url"):
                st.image(channel_profile["thumbnail_url"], width=72)
            st.markdown(
                f"""
                <div class="sidebar-card">
                    <strong>{channel_profile.get("title", "Connected Channel")}</strong>
                    <p>{channel_profile.get("handle", "Authorized YouTube profile")}</p>
                    <p>{int(channel_profile.get("subscriber_count", "0")):,} subscribers | {int(channel_profile.get("video_count", "0")):,} videos</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif channel_message:
            st.caption(channel_message)

        st.markdown('<div class="sidebar-section">Navigation</div>', unsafe_allow_html=True)
        selected_view = st.radio(
            "Navigation",
            options=PAGE_LABELS,
            key="selected_view",
            label_visibility="collapsed",
        )

        vault = st.session_state.vault_settings
        st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sidebar-card">
                <strong>Model</strong>
                <p>{vault.get("ollama_model", "Not set")}</p>
                <div class="sidebar-status-grid">
                    <div class="sidebar-status-pill">
                        <strong>Data</strong>
                        <span>Live YouTube</span>
                    </div>
                    <div class="sidebar-status-pill">
                        <strong>Style</strong>
                        <span>{st.session_state.get("coach_response_style", "Concise")}</span>
                    </div>
                    <div class="sidebar-status-pill">
                        <strong>Token</strong>
                        <span>{"Connected" if has_saved_token() else "Missing"}</span>
                    </div>
                    <div class="sidebar-status-pill">
                        <strong>Mode</strong>
                        <span>Private Local</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.selectbox(
            "A.R.I.A. response style",
            options=["Concise", "Standard", "Deep"],
            key="coach_response_style",
            help="Controls how short or detailed A.R.I.A. should be across coaching and generation.",
        )

    return selected_view


def render_quick_jump_bar(selected_view: str) -> None:
    global_labels = ["Today Desk", "Upload Radar", "Request Signals"]
    contextual_labels = CONTEXTUAL_JUMP_GROUPS.get(selected_view, [])
    ordered_labels: list[str] = []
    for label in global_labels + contextual_labels:
        if label not in ordered_labels:
            ordered_labels.append(label)

    st.markdown(
        """
        <div class="jumpbar-shell">
            <div>
                <div class="jumpbar-title">Quick Jump</div>
                <div class="jumpbar-copy">Global shortcuts stay visible, and the rest of the jump bar adapts to your current workspace.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(ordered_labels))
    for col, label in zip(cols, ordered_labels):
        with col:
            if st.button(label, key=f"quick_jump_{label.lower().replace(' ', '_')}", use_container_width=True):
                for state_key, state_value in QUICK_JUMP_TARGETS[label].items():
                    st.session_state[state_key] = state_value
                st.rerun()


def render_section_header(chip: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-chip">{chip}</div>
        <div class="section-title">{title}</div>
        <div class="section-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def render_creator_hero(
    channel_name: str,
    handle: str,
    summary: str,
    stats: list[tuple[str, str, str]],
    status: str,
) -> None:
    stat_markup = "".join(
        f"""
        <div class="creator-hero-stat">
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{meta}</small>
        </div>
        """
        for label, value, meta in stats
    )
    st.markdown(
        f"""
        <div class="creator-hero">
            <div class="creator-hero-main">
                <div class="creator-eyebrow">Creator Command Dashboard</div>
                <h1>{channel_name}</h1>
                <p>{summary}</p>
                <div class="creator-hero-meta">
                    <span>{handle}</span>
                    <span>{status}</span>
                    <span>Private local studio</span>
                </div>
            </div>
            <div class="creator-hero-stats">
                {stat_markup}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_strip(title: str, copy: str, pills: list[str]) -> None:
    pill_markup = "".join(f'<div class="masthead-pill">{pill}</div>' for pill in pills)
    st.markdown(
        f"""
        <div class="action-strip">
            <div>
                <div class="action-strip-title">{title}</div>
                <div class="action-strip-copy">{copy}</div>
            </div>
            <div class="action-strip-pills">{pill_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_leaderboard_card(title: str, rows: list[tuple[str, str]], dense: bool = True) -> None:
    items = "".join(
        f"""
        <div class="leaderboard-row">
            <div class="leaderboard-label">{label}</div>
            <div class="leaderboard-value">{value}</div>
        </div>
        """
        for label, value in rows
    )
    density_class = " leaderboard-dense" if dense else ""
    st.markdown(
        f"""
        <div class="leaderboard-card{density_class}">
            <div class="leaderboard-title">{title}</div>
            {items}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: str, meta: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(title: str, value: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="panel-shell">
            <div class="panel-title">{title}</div>
            <div class="panel-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_song_snapshot(selected_row) -> None:
    import pandas as pd

    target = (
        selected_row["target_upload_date"].strftime("%Y-%m-%d")
        if pd.notna(selected_row["target_upload_date"])
        else "Unscheduled"
    )
    pillar = selected_row["content_pillar"] or "Unlabeled"
    notes = selected_row["notes"] or "No notes yet."
    st.markdown(
        f"""
        <div class="snapshot-card">
            <div class="snapshot-title">{selected_row["title"]}</div>
            <div class="snapshot-tags">
                <div class="snapshot-tag">{selected_row["stage"]}</div>
                <div class="snapshot-tag">{selected_row["priority"]} priority</div>
                <div class="snapshot-tag">{pillar}</div>
                <div class="snapshot-tag">{target}</div>
            </div>
            <div class="snapshot-notes">{notes}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_editorial_list(title: str, rows: list[tuple[str, str]]) -> None:
    items = "".join(
        f'<div class="editorial-item"><span>{label}</span><span>{value}</span></div>'
        for label, value in rows
    )
    st.markdown(f"**{title}**")
    st.markdown(f'<div class="editorial-list">{items}</div>', unsafe_allow_html=True)


def render_status_strip(items: list[tuple[str, str]]) -> None:
    if not items:
        return
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            render_insight_card(label, str(value), "")
