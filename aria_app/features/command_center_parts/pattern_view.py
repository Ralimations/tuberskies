from __future__ import annotations

import pandas as pd
import streamlit as st

from aria_app.ui import render_editorial_list, render_insight_card, render_panel_header

def render_pattern_memory(snapshot: dict[str, object]) -> None:
    render_panel_header(
        "Pattern Memory",
        "A.R.I.A.'s local memory layer. It turns live signals and repertoire habits into quick guidance you can reuse.",
    )

    if not snapshot:
        st.info("Pattern Memory has not stored a snapshot yet.")
        return

    publish_memory = snapshot.get("publish_memory", {})
    stage_memory = snapshot.get("stage_memory", {})
    title_patterns = snapshot.get("title_patterns", [])
    pillar_memory = snapshot.get("pillar_memory", [])
    repeat_more = snapshot.get("repeat_more", [])
    reduce_or_fix = snapshot.get("reduce_or_fix", [])

    col1, col2, col3 = st.columns(3)
    with col1:
        render_insight_card(
            "Best Day to Push",
            str(publish_memory.get("best_day", "Unknown")),
            f"Local publish score: {publish_memory.get('best_score', '--')}",
        )
    with col2:
        render_insight_card(
            "Main Bottleneck",
            str(stage_memory.get("bottleneck_stage", "Unknown")),
            f"{stage_memory.get('bottleneck_count', 0)} item(s) currently stacked here.",
        )
    with col3:
        render_insight_card(
            "Overdue Queue",
            str(stage_memory.get("overdue_count", 0)),
            "Active repertoire items that are behind target date.",
        )

    left, right = st.columns([1.15, 0.85])
    with left:
        render_editorial_list(
            "Repeat More Often",
            [(f"Pattern {index}", item) for index, item in enumerate(repeat_more, start=1)] or [("Status", "No repeat recommendations yet.")],
        )
        render_editorial_list(
            "Reduce or Fix",
            [(f"Focus {index}", item) for index, item in enumerate(reduce_or_fix, start=1)] or [("Status", "No friction patterns detected yet.")],
        )
    with right:
        render_editorial_list(
            "Top Title Patterns",
            [(item.get("pattern", "Unknown"), f"{item.get('type', 'pattern')} x{item.get('count', 0)}") for item in title_patterns] or [("Status", "No title patterns yet.")],
        )
        render_editorial_list(
            "Content Pillars in Rotation",
            [(item.get("pillar", "Unknown"), f"{item.get('count', 0)} project(s)") for item in pillar_memory] or [("Status", "No pillar tags yet.")],
        )

    weekday_rows = publish_memory.get("weekday_rows", [])
    if weekday_rows:
        st.markdown("### Weekday Scoreboard")
        st.dataframe(pd.DataFrame(weekday_rows), use_container_width=True, hide_index=True)

    niche_hint = str(snapshot.get("niche_hint", "")).strip()
    if niche_hint:
        st.caption(f"Latest Niche Lab lead remembered: {niche_hint}")
