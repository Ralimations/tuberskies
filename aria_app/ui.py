from __future__ import annotations

from urllib.parse import quote, urlencode

import streamlit as st

from .navigation import PAGE_LABELS, SIDEBAR_TOOLS
from .theme import APP_CSS


SECTION_QUERY_KEYS = {
    "command_center_section": {"Dashboard", "Analytics", "Pattern Memory", "Upload Lab"},
    "upload_lab_section": {"Summary", "History", "Momentum", "Radar"},
    "momentum_workspace_section": {"Snapshot", "Scoreboards", "Trend Watch"},
}

ICON_PATHS = {
    "home": '<path d="M3 9.5 12 3l9 6.5v10a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H4.5A1.5 1.5 0 0 1 3 19.5z"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "chart": '<path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 4-4 3 3 5-7"/>',
    "upload": '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M5 18h14"/>',
    "memory": '<path d="M5 7h14M5 12h14M5 17h10"/><path d="M4 4h16v16H4z"/>',
    "spark": '<path d="M12 2v5M12 17v5M4.9 4.9l3.5 3.5M15.6 15.6l3.5 3.5M2 12h5M17 12h5M4.9 19.1l3.5-3.5M15.6 8.4l3.5-3.5"/>',
    "signal": '<path d="M4 18c4-8 12-8 16 0"/><path d="M8 18c2-4 6-4 8 0"/><path d="M12 18h.01"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "music": '<path d="M9 18V5l10-2v13"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>',
    "calendar": '<path d="M5 5h14v15H5z"/><path d="M8 3v4M16 3v4M5 9h14"/>',
    "clipping": '<circle cx="6" cy="7" r="3"/><circle cx="6" cy="17" r="3"/><path d="M8.5 8.5 20 20M8.5 15.5 20 4"/>',
    "scissors": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5 19 19M8.5 15.5 19 5"/>',
    "vault": '<path d="M4 7h16v13H4z"/><path d="M8 7V5a4 4 0 0 1 8 0v2"/><circle cx="12" cy="13.5" r="2.5"/>',
    "comments": '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h6"/>',
}


def inject_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def _query_value(key: str) -> str:
    value = st.query_params.get(key, "")
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _normalize_view(value: str) -> str:
    lowered = value.lower()
    for label in PAGE_LABELS:
        if label.lower() == lowered:
            return label
    return PAGE_LABELS[0]


def _apply_sidebar_query_params() -> str:
    selected_view = _normalize_view(_query_value("view") or st.session_state.get("selected_view", PAGE_LABELS[0]))
    st.session_state.selected_view = selected_view
    for key, allowed_values in SECTION_QUERY_KEYS.items():
        value = _query_value(key)
        if value in allowed_values:
            st.session_state[key] = value
    return selected_view


def _nav_href(params: dict[str, str]) -> str:
    return f"?{urlencode(params, quote_via=quote)}"


def _nav_icon(name: str) -> str:
    path = ICON_PATHS.get(name, ICON_PATHS["home"])
    return f'<svg class="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">{path}</svg>'


def _is_sidebar_item_active(params: dict[str, str], selected_view: str) -> bool:
    if params.get("view") != selected_view:
        return False
    for key, expected in params.items():
        if key == "view":
            continue
        if st.session_state.get(key) != expected:
            return False
    return True


def render_header_navigation() -> str:
    selected_view = _apply_sidebar_query_params()

    group_markup = ""
    for group_data in SIDEBAR_TOOLS:
        group = group_data["group"]
        links = ""
        for label, icon_name, params in group_data["items"]:
            active_class = " active" if _is_sidebar_item_active(params, selected_view) else ""
            links += (
                f'<a class="header-menu-link{active_class}" href="{_nav_href(params)}" target="_self">'
                f'{_nav_icon(icon_name)}'
                f'<span>{label}</span>'
                '</a>'
            )
        group_markup += (
            f'<div class="header-menu-group">'
            f'<div class="header-menu-label">{group}</div>'
            f'<div class="header-menu-links">{links}</div>'
            f'</div>'
        )

    shell_markup = (
        '<div class="app-shell">'
        '<aside class="app-sidebar">'
        '<div class="sidebar-brand">'
        '<div class="appbar-mark">A</div>'
        '<div class="sidebar-brand-text">A.R.I.A.</div>'
        '</div>'
        f'<div class="header-menu-shell">{group_markup}</div>'
        '<div class="sidebar-upgrade">Local-first creator intelligence</div>'
        '</aside>'
        '</div>'
    )
    st.markdown(shell_markup, unsafe_allow_html=True)
    return selected_view


def render_section_header(chip: str, title: str, copy: str) -> None:
    markup = f'<div class="section-chip">{chip}</div><div class="section-title">{title}</div><div class="section-copy">{copy}</div>'
    st.markdown(markup, unsafe_allow_html=True)


def render_creator_hero(
    channel_name: str,
    handle: str,
    summary: str,
    stats: list[tuple[str, str, str]],
    status: str,
) -> None:
    stat_markup = "".join(
        f'<div class="creator-hero-stat"><span>{label}</span><strong>{value}</strong><small>{meta}</small></div>'
        for label, value, meta in stats
    )
    hero_markup = (
        '<div class="creator-hero">'
        '<div class="creator-hero-main">'
        '<div class="creator-eyebrow">Macro pulse</div>'
        f'<h1>{channel_name}</h1>'
        f'<p>{summary}</p>'
        '<div class="creator-hero-meta">'
        f'<span>{handle}</span>'
        f'<span>{status}</span>'
        '<span>Local analytics memory</span>'
        '</div>'
        '</div>'
        f'<div class="creator-hero-stats">{stat_markup}</div>'
        '</div>'
    )
    st.markdown(hero_markup, unsafe_allow_html=True)


def render_action_strip(title: str, copy: str, pills: list[str]) -> None:
    pill_markup = "".join(f'<div class="masthead-pill">{pill}</div>' for pill in pills)
    markup = (
        '<div class="action-strip">'
        f'<div><div class="action-strip-title">{title}</div><div class="action-strip-copy">{copy}</div></div>'
        f'<div class="action-strip-pills">{pill_markup}</div>'
        '</div>'
    )
    st.markdown(markup, unsafe_allow_html=True)


def render_leaderboard_card(title: str, rows: list[tuple[str, str]], dense: bool = True) -> None:
    items = "".join(
        f'<div class="leaderboard-row"><div class="leaderboard-label">{label}</div><div class="leaderboard-value">{value}</div></div>'
        for label, value in rows
    )
    density_class = " leaderboard-dense" if dense else ""
    markup = f'<div class="leaderboard-card{density_class}"><div class="leaderboard-title">{title}</div>{items}</div>'
    st.markdown(markup, unsafe_allow_html=True)


def render_stat_card(label: str, value: str, meta: str) -> None:
    markup = f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{value}</div><div class="stat-meta">{meta}</div></div>'
    st.markdown(markup, unsafe_allow_html=True)


def render_insight_card(title: str, value: str, copy: str) -> None:
    markup = f'<div class="insight-card"><div class="insight-title">{title}</div><div class="insight-value">{value}</div><div class="insight-copy">{copy}</div></div>'
    st.markdown(markup, unsafe_allow_html=True)


def render_panel_header(title: str, copy: str) -> None:
    markup = f'<div class="panel-shell"><div class="panel-title">{title}</div><div class="panel-copy">{copy}</div></div>'
    st.markdown(markup, unsafe_allow_html=True)


def render_song_snapshot(selected_row) -> None:
    import pandas as pd

    target = (
        selected_row["target_upload_date"].strftime("%Y-%m-%d")
        if pd.notna(selected_row["target_upload_date"])
        else "Unscheduled"
    )
    pillar = selected_row["content_pillar"] or "Unlabeled"
    notes = selected_row["notes"] or "No notes yet."
    markup = (
        '<div class="snapshot-card">'
        f'<div class="snapshot-title">{selected_row["title"]}</div>'
        '<div class="snapshot-tags">'
        f'<div class="snapshot-tag">{selected_row["stage"]}</div>'
        f'<div class="snapshot-tag">{selected_row["priority"]} priority</div>'
        f'<div class="snapshot-tag">{pillar}</div>'
        f'<div class="snapshot-tag">{target}</div>'
        '</div>'
        f'<div class="snapshot-notes">{notes}</div>'
        '</div>'
    )
    st.markdown(markup, unsafe_allow_html=True)


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
