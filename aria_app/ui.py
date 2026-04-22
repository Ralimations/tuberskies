from __future__ import annotations

import streamlit as st

from .theme import APP_CSS
from .navigation import PAGE_LABELS


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
                <div class="appbar-mark">A</div>
                <div>
                    <div class="appbar-title">A.R.I.A. Analytics</div>
                    <div class="appbar-copy">Signal-first workspace for channel decisions.</div>
                </div>
            </div>
            <div class="appbar-nav-anchor">Navigation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header_navigation() -> str:
    if st.session_state.get("selected_view") not in PAGE_LABELS:
        st.session_state.selected_view = PAGE_LABELS[0]

    selected_view = st.segmented_control(
        "Studio Areas",
        options=PAGE_LABELS,
        key="selected_view",
        label_visibility="collapsed",
    )
    if selected_view is None:
        selected_view = st.session_state.get("selected_view", PAGE_LABELS[0])
    return str(selected_view)


def render_quick_jump_bar(selected_view: str) -> None:
    return


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
                <div class="creator-eyebrow">Macro pulse</div>
                <h1>{channel_name}</h1>
                <p>{summary}</p>
                <div class="creator-hero-meta">
                    <span>{handle}</span>
                    <span>{status}</span>
                    <span>Local analytics memory</span>
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
