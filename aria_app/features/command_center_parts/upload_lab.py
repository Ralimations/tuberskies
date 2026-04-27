from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import render_action_strip, render_editorial_list, render_insight_card, render_leaderboard_card, render_panel_header
from aria_app.features.command_center_parts.upload_metrics import (
    build_format_rows,
    build_franchise_heatmap_rows,
    build_upload_takeaways,
)
from aria_app.features.command_center_parts.upload_momentum import (
    build_month_options,
    build_trend_queries,
    extract_topic_rows,
    filter_videos_for_month,
    render_momentum_planner,
)
from aria_app.features.command_center_parts.upload_radar import render_next_cover_radar
from youtube_cache import cached_music_trends

def render_upload_lab(video_df: pd.DataFrame, upload_message: str) -> None:
    render_panel_header(
        "Upload Lab",
        "A.R.I.A.'s per-upload board. This is where we inspect what your previous releases actually did and what patterns deserve repeating.",
    )

    if video_df is None or video_df.empty:
        st.info(upload_message or "No upload-level performance data is available yet.")
        return

    takeaways = build_upload_takeaways(video_df)
    best = takeaways["best"]
    weak = takeaways["weak"]
    compact_df = video_df.copy()
    compact_df["published_at"] = compact_df["published_at"].dt.strftime("%Y-%m-%d")
    numeric_cols = ["views", "watch_time_hours", "subscribers_gained", "like_count", "comment_count", "engagement_score", "retention"]
    for column in numeric_cols:
        if column in compact_df.columns:
            compact_df[column] = compact_df[column].round(1)

    col1, col2, col3 = st.columns(3)
    with col1:
        render_insight_card(
            "Best Upload in Window",
            str(best["title"]),
            f"{int(best['views']):,} views | {best['retention']:.1f}% retention | score {best['engagement_score']:.1f}",
        )
    with col2:
        render_insight_card(
            "Weakest Upload in Window",
            str(weak["title"]),
            f"{int(weak['views']):,} views | {weak['retention']:.1f}% retention | score {weak['engagement_score']:.1f}",
        )
    with col3:
        render_insight_card(
            "Uploads in View",
            f"{len(video_df):,}",
            "Use the workspace below to switch between summary, history, momentum, and radar.",
        )

    render_action_strip(
        "Upload Workspace",
        "Switch between overview, full history, momentum analysis, and next-cover decisions without leaving the page.",
        ["Summary First", "History On Demand", "Radar Ready"],
    )

    upload_section = st.session_state.upload_lab_section
    st.markdown('<div class="compact-note">Professional dashboards keep one decision surface visible at a time. This workspace now does the same.</div>', unsafe_allow_html=True)

    if upload_section == "Summary":
        preview_rows = [
            (str(best["title"])[:42], f"{int(best['views']):,} views"),
            (str(weak["title"])[:42], f"{int(weak['views']):,} views"),
            ("Average Retention", f"{video_df['retention'].mean():.1f}%"),
            ("Subscribers Gained", f"{int(video_df['subscribers_gained'].fillna(0).sum()):,}"),
        ]
        left, center, right = st.columns([0.95, 1.05, 0.8])
        with left:
            render_editorial_list("Quick Read", preview_rows)
            summary_rows = []
            for _, row in compact_df.head(5)[["published_at", "title", "views"]].iterrows():
                summary_rows.append((f'{row["published_at"]} | {str(row["title"])[:34]}', f'{int(row["views"]):,}'))
            render_leaderboard_card("Top In View", summary_rows)
        with center:
            render_editorial_list("What Seems to Work", takeaways["pattern_rows"] or [("Status", "A.R.I.A. needs more upload data to detect winners.")])
            render_editorial_list("What to Improve", takeaways["improvement_rows"] or [("Status", "No clear weak pattern yet.")])
        with right:
            render_editorial_list(
                "Best vs Weak",
                [
                    ("Best", str(best["title"])[:40]),
                    ("Weakest", str(weak["title"])[:40]),
                    ("Best Score", f"{best['engagement_score']:.1f}"),
                    ("Weak Score", f"{weak['engagement_score']:.1f}"),
                ],
            )
            if st.button("Ask A.R.I.A. to Review Upload History", key="upload_lab_coach"):
                model = st.session_state.vault_settings.get("ollama_model", "gemma")
                sample = video_df.head(10)[["title", "views", "retention", "watch_time_hours", "subscribers_gained", "engagement_score"]].to_csv(index=False)
                prompt = textwrap.dedent(
                    f"""
                    Review this upload history for Ralskies.
                    Keep it practical and concise.
                    Explain:
                    1. What seems to work best
                    2. What seems weaker
                    3. Which title or framing patterns deserve repeating
                    4. One improvement for the next upload

                    Upload data:
                    {sample}
                    """
                ).strip()
                with st.chat_message("assistant"):
                    st.write_stream(stream_aria_response(prompt, model))
        return

    if upload_section == "History":
        st.dataframe(compact_df, use_container_width=True, hide_index=True)
        return

    if upload_section == "Momentum":
        render_momentum_planner(video_df, st.session_state.vault_settings)
        return

    month_options = build_month_options(video_df)
    selected_month = month_options[0] if month_options else ""
    monthly_df = filter_videos_for_month(video_df, selected_month) if selected_month else video_df.head(0)
    monthly_topics = extract_topic_rows(monthly_df) if not monthly_df.empty else []
    trend_queries = build_trend_queries(monthly_topics, monthly_df) if not monthly_df.empty else []
    trend_df, _ = cached_music_trends(st.session_state.vault_settings, trend_queries) if trend_queries else (None, "No trend queries")
    render_next_cover_radar(
        monthly_df=monthly_df,
        monthly_franchises=build_franchise_heatmap_rows(monthly_df) if not monthly_df.empty else [],
        global_franchises=build_franchise_heatmap_rows(video_df),
        monthly_formats=build_format_rows(monthly_df) if not monthly_df.empty else [],
        trend_df=trend_df,
    )
