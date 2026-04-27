from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import render_editorial_list, render_insight_card, render_panel_header
from aria_app.features.command_center_parts.upload_metrics import (
    build_gap_rows,
)

def build_next_cover_radar(
    monthly_df: pd.DataFrame,
    monthly_franchises: list[dict[str, object]],
    global_franchises: list[dict[str, object]],
    monthly_formats: list[dict[str, object]],
    trend_df: pd.DataFrame | None,
    niche_output: str,
) -> list[dict[str, object]]:
    radar_rows: list[dict[str, object]] = []
    gap_rows = build_gap_rows(monthly_df, global_franchises)

    hottest_franchise = monthly_franchises[0]["franchise"] if monthly_franchises else (global_franchises[0]["franchise"] if global_franchises else "General / Mixed")
    best_format = monthly_formats[0]["format"] if monthly_formats else "Produced Cover"
    trend_titles = trend_df["title"].fillna("").astype(str).head(8).tolist() if trend_df is not None and not trend_df.empty else []

    franchise_idea_map = {
        "Hazbin Hotel": "a dramatic Hazbin character ballad or duet",
        "Epic / Ilium": "an Epic / Ilium theatrical cover with stronger storytelling framing",
        "K-Pop Demon Hunters": "a Demon Hunters english-version or emotional reinterpretation",
        "Original Universe": "a dreamy original with celestial branding",
        "General / Mixed": "a cover built around your strongest vocal-theatre lane",
    }
    franchise_match_map = {
        "Hazbin Hotel": ["hazbin", "gravity", "brighter", "losing streak"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Original Universe": ["original", "dream", "stars"],
    }

    radar_rows.append(
        {
            "lane": "Best Next Move",
            "franchise": hottest_franchise,
            "format": best_format,
            "confidence": "High",
            "idea": franchise_idea_map.get(hottest_franchise, "a theatrical cover in your strongest lane"),
            "why": f"{hottest_franchise} is your strongest current or recent franchise signal, and {best_format} is the strongest format read.",
        }
    )

    if gap_rows:
        top_gap = gap_rows[0]
        radar_rows.append(
            {
                "lane": "Safe Momentum Recovery",
                "franchise": top_gap["franchise"],
                "format": best_format,
                "confidence": "Medium",
                "idea": franchise_idea_map.get(top_gap["franchise"], "a return-to-form cover idea"),
                "why": top_gap["gap_note"],
            }
        )

    if trend_titles:
        preferred_title = trend_titles[0]
        preferred_keywords = franchise_match_map.get(hottest_franchise, [])
        for title in trend_titles:
            lowered = title.lower()
            if any(keyword in lowered for keyword in preferred_keywords):
                preferred_title = title
                break
        radar_rows.append(
            {
                "lane": "Riskier Upside Bet",
                "franchise": hottest_franchise,
                "format": "Trend-Adjacent Cover",
                "confidence": "Exploratory",
                "idea": preferred_title,
                "why": "This comes from current niche-adjacent YouTube trend search and could catch fresh discovery.",
            }
        )

    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in radar_rows:
        key = (str(row["lane"]), str(row["idea"]))
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped[:4]


def render_next_cover_radar(
    monthly_df: pd.DataFrame,
    monthly_franchises: list[dict[str, object]],
    global_franchises: list[dict[str, object]],
    monthly_formats: list[dict[str, object]],
    trend_df: pd.DataFrame | None,
) -> None:
    render_panel_header(
        "Next Cover Radar",
        "A.R.I.A.'s recommendation layer. It combines franchise heat, format strength, recent upload gaps, and niche trends into concrete next-move options.",
    )

    radar_rows = build_next_cover_radar(
        monthly_df=monthly_df,
        monthly_franchises=monthly_franchises,
        global_franchises=global_franchises,
        monthly_formats=monthly_formats,
        trend_df=trend_df,
        niche_output=st.session_state.niche_output,
    )
    gap_rows = build_gap_rows(monthly_df, global_franchises)

    if not radar_rows:
        st.info("A.R.I.A. needs a little more upload history or niche context before it can build the radar.")
        return

    top_cols = st.columns(len(radar_rows))
    for col, row in zip(top_cols, radar_rows):
        with col:
            render_insight_card(
                str(row["lane"]),
                str(row["franchise"]),
                f"{row['format']} | {row['confidence']}\n{row['idea']}",
            )

    left, right = st.columns([1.2, 0.8])
    with left:
        radar_table = pd.DataFrame(radar_rows)[["lane", "franchise", "format", "confidence", "idea", "why"]]
        st.dataframe(radar_table, use_container_width=True, hide_index=True)
    with right:
        render_editorial_list(
            "Opportunity Gaps",
            [(row["franchise"], row["gap_note"]) for row in gap_rows[:4]] or [("Status", "No major franchise gap detected this month.")],
        )

    if st.button("Ask A.R.I.A. for the Best Next Cover", key="next_cover_radar_coach"):
        model = st.session_state.vault_settings.get("ollama_model", "gemma")
        radar_csv = pd.DataFrame(radar_rows).to_csv(index=False)
        gap_csv = pd.DataFrame(gap_rows).to_csv(index=False) if gap_rows else "No major gaps."
        trend_csv = trend_df[["query", "title", "channel_title"]].head(8).to_csv(index=False) if trend_df is not None and not trend_df.empty else "No trend videos."
        prompt = textwrap.dedent(
            f"""
            Review this Next Cover Radar for Ralskies.
            Keep the answer concise and practical.
            Return:
            1. The single best next cover or song move
            2. Why it is the best move right now
            3. One safer fallback
            4. One riskier upside option
            5. A suggested title angle for the best move

            Radar candidates:
            {radar_csv}

            Opportunity gaps:
            {gap_csv}

            Related trend videos:
            {trend_csv}
            """
        ).strip()
        with st.chat_message("assistant"):
            st.write_stream(stream_aria_response(prompt, model))
