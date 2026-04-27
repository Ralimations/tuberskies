from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_aria_response
from aria_app.ui import render_editorial_list, render_insight_card, render_leaderboard_card, render_panel_header
from aria_app.features.command_center_parts.upload_metrics import (
    build_archetype_recommendations,
    build_archetype_rows,
    build_format_rows,
    build_franchise_heatmap_rows,
    build_heatmap_recommendations,
)
from youtube_cache import cached_music_trends

def build_month_options(video_df: pd.DataFrame) -> list[str]:
    if video_df is None or video_df.empty or video_df["published_at"].dropna().empty:
        return []
    published = pd.to_datetime(video_df["published_at"], errors="coerce")
    if getattr(published.dt, "tz", None) is not None:
        published = published.dt.tz_localize(None)
    months = (
        published.dropna()
        .dt.to_period("M")
        .astype(str)
        .drop_duplicates()
        .sort_values(ascending=False)
        .tolist()
    )
    return months


def filter_videos_for_month(video_df: pd.DataFrame, month_key: str) -> pd.DataFrame:
    if video_df is None or video_df.empty or not month_key:
        return pd.DataFrame(columns=video_df.columns if video_df is not None else [])
    month_period = pd.Period(month_key, freq="M")
    published = pd.to_datetime(video_df["published_at"], errors="coerce")
    if getattr(published.dt, "tz", None) is not None:
        published = published.dt.tz_localize(None)
    filtered = video_df[published.dt.to_period("M") == month_period].copy()
    return filtered.sort_values("published_at", ascending=False).reset_index(drop=True)


def extract_topic_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    patterns = {
        "Hazbin Hotel": ["hazbin"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "English Version": ["english version", "english ver", "english"],
        "Male Version": ["male version", "male cover", "male"],
        "Original Music": ["into the stars", "dreaming", "original"],
        "Cover Performance": ["cover", "reimagined"],
    }

    rows: list[dict[str, object]] = []
    titles = video_df["title"].fillna("").astype(str)
    for topic, keywords in patterns.items():
        mask = titles.str.lower().apply(lambda value: any(keyword in value for keyword in keywords))
        subset = video_df[mask]
        if subset.empty:
            continue
        rows.append(
            {
                "topic": topic,
                "uploads": int(len(subset)),
                "avg_views": round(float(subset["views"].mean()), 1),
                "avg_retention": round(float(subset["retention"].mean()), 2),
                "avg_engagement_score": round(float(subset["engagement_score"].mean()), 1),
                "total_subscribers": int(subset["subscribers_gained"].fillna(0).sum()),
            }
        )

    rows.sort(key=lambda row: (row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_trend_queries(topic_rows: list[dict[str, object]], monthly_df: pd.DataFrame) -> list[str]:
    queries: list[str] = []
    for row in topic_rows[:3]:
        topic = str(row.get("topic", ""))
        if topic == "Hazbin Hotel":
            queries.append("Hazbin Hotel cover song")
        elif topic == "Epic / Ilium":
            queries.append("Epic the Musical cover")
            queries.append("Ilium musical cover")
        elif topic == "K-Pop Demon Hunters":
            queries.append("KPop Demon Hunters cover")
            queries.append("Saja Boys english version")
        elif topic == "English Version":
            queries.append("anime song english version cover")
        elif topic == "Male Version":
            queries.append("male version cover song")
        elif topic == "Original Music":
            queries.append("dreamy indie pop ballad")

    if monthly_df is not None and not monthly_df.empty:
        top_title = str(monthly_df.sort_values("engagement_score", ascending=False).iloc[0]["title"]).lower()
        if "gravity" in top_title:
            queries.append("Hazbin Hotel gravity cover")
        if "fire" in top_title:
            queries.append("Ilium fire cover")
        if "your idol" in top_title:
            queries.append("Your Idol english version cover")

    deduped: list[str] = []
    for query in queries:
        if query not in deduped:
            deduped.append(query)
    return deduped[:4]


def build_momentum_ideas(topic_rows: list[dict[str, object]], trend_df: pd.DataFrame | None) -> list[tuple[str, str]]:
    ideas: list[tuple[str, str]] = []
    for row in topic_rows[:3]:
        topic = str(row.get("topic", ""))
        if topic == "Hazbin Hotel":
            ideas.append(("Stay in Hazbin", "Follow your strongest theatrical lane with another dramatic Hazbin-focused cover or duet."))
        elif topic == "Epic / Ilium":
            ideas.append(("Lean into Epic", "An Epic or Ilium follow-up looks aligned with your theatrical audience and vocal style."))
        elif topic == "K-Pop Demon Hunters":
            ideas.append(("Ride the fandom wave", "Another Demon Hunters or Saja Boys angle could keep current attention warm."))
        elif topic == "English Version":
            ideas.append(("Keep translation framing", "English-version packaging is readable and shareable for discovery traffic."))
        elif topic == "Male Version":
            ideas.append(("Repeat the reimagining", "A male-version reinterpretation still fits your strongest channel identity."))

    if trend_df is not None and not trend_df.empty:
        trend_titles = trend_df["title"].fillna("").astype(str).head(3).tolist()
        for title in trend_titles:
            ideas.append(("Trend-adjacent option", f"Consider a {st.session_state.vault_settings.get('CHANNEL_NAME', 'Ralskies')} spin on: {title}"))

    deduped: list[tuple[str, str]] = []
    for item in ideas:
        if item not in deduped:
            deduped.append(item)
    return deduped[:5]


def render_momentum_planner(video_df: pd.DataFrame, settings: dict[str, str]) -> None:
    render_panel_header(
        "Momentum Planner",
        "Review this month's uploads, see which topics carried traction, and line up the next song or cover while the niche is still warm.",
    )

    if video_df is None or video_df.empty:
        st.info("Upload-level data is needed before A.R.I.A. can map monthly momentum.")
        return

    month_options = build_month_options(video_df)
    if not month_options:
        st.info("No dated uploads were returned in the current window.")
        return

    selected_month = st.selectbox("Month to inspect", options=month_options, key="momentum_month")
    monthly_df = filter_videos_for_month(video_df, selected_month)
    if monthly_df.empty:
        st.info("No uploads were found for that month.")
        return

    recent_five = monthly_df.head(5).copy()
    topic_rows = extract_topic_rows(monthly_df)
    monthly_archetypes = build_archetype_rows(monthly_df)
    global_archetypes = build_archetype_rows(video_df)
    archetype_recommendations = build_archetype_recommendations(monthly_archetypes, global_archetypes)
    monthly_formats = build_format_rows(monthly_df)
    global_formats = build_format_rows(video_df)
    monthly_franchises = build_franchise_heatmap_rows(monthly_df)
    global_franchises = build_franchise_heatmap_rows(video_df)
    heatmap_recommendations = build_heatmap_recommendations(monthly_franchises, global_formats)
    trend_queries = build_trend_queries(topic_rows, monthly_df)
    trend_df, trend_message = cached_music_trends(settings, trend_queries) if trend_queries else (None, "No trend queries available yet.")
    momentum_ideas = build_momentum_ideas(topic_rows, trend_df)

    col1, col2, col3 = st.columns(3)
    with col1:
        render_insight_card("Uploads This Month", str(len(monthly_df)), "How many scored uploads landed in the selected month.")
    with col2:
        best_topic_value = monthly_franchises[0]["franchise"] if monthly_franchises else (topic_rows[0]["topic"] if topic_rows else "Not enough data")
        render_insight_card("Hottest Franchise", best_topic_value, "Strongest recency-weighted momentum in the selected month.")
    with col3:
        top_video = monthly_df.sort_values("engagement_score", ascending=False).iloc[0]
        render_insight_card("Top Upload", str(top_video["title"]), f"Score {top_video['engagement_score']:.1f} | {int(top_video['views']):,} views")

    momentum_section = st.session_state.momentum_workspace_section

    if momentum_section == "Snapshot":
        left, right = st.columns([1.2, 0.8])
        with left:
            recent_rows = []
            for _, row in recent_five.iterrows():
                recent_rows.append((str(row["title"])[:44], f"{int(row['views']):,} views"))
            render_leaderboard_card("Recent Uploads", recent_rows or [("Status", "No recent uploads")])

            if topic_rows:
                topic_leader_rows = [(str(row["topic"]), f"{int(row['uploads'])} uploads | {row['avg_views']:,.0f} avg views") for row in topic_rows[:6]]
                render_leaderboard_card("Topic Traction", topic_leader_rows)
            else:
                st.info("A.R.I.A. could not confidently cluster month topics yet.")
        with right:
            render_editorial_list("Momentum Ideas", momentum_ideas or [("Status", "No next-step ideas were generated yet.")])
            render_editorial_list("Archetype Guidance", archetype_recommendations or [("Status", "No clear archetype recommendation yet.")])
            render_editorial_list("Franchise Heat Guidance", heatmap_recommendations or [("Status", "No clear franchise heat recommendation yet.")])
        return

    if momentum_section == "Scoreboards":
        left, right = st.columns(2)
        with left:
            if monthly_archetypes:
                st.dataframe(pd.DataFrame(monthly_archetypes), use_container_width=True, hide_index=True)
            else:
                st.info("No monthly archetype table yet.")
            if monthly_franchises:
                st.dataframe(pd.DataFrame(monthly_franchises), use_container_width=True, hide_index=True)
            else:
                st.info("No monthly franchise heatmap yet.")
        with right:
            if global_archetypes:
                st.dataframe(pd.DataFrame(global_archetypes[:8]), use_container_width=True, hide_index=True)
            else:
                st.info("No broader archetype table yet.")
            if monthly_formats:
                st.dataframe(pd.DataFrame(monthly_formats), use_container_width=True, hide_index=True)
            else:
                st.info("No monthly format split yet.")
        return

    left, right = st.columns([0.95, 1.05])
    with left:
        if trend_queries:
            render_editorial_list("Trend Queries", [(f"Query {index}", query) for index, query in enumerate(trend_queries, start=1)])
        if st.button("Ask A.R.I.A. for a Momentum Plan", key="momentum_plan_coach"):
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            topic_csv = pd.DataFrame(topic_rows).head(6).to_csv(index=False) if topic_rows else "No topic clusters."
            monthly_archetype_csv = pd.DataFrame(monthly_archetypes).head(8).to_csv(index=False) if monthly_archetypes else "No monthly archetypes."
            global_archetype_csv = pd.DataFrame(global_archetypes).head(8).to_csv(index=False) if global_archetypes else "No broader archetypes."
            monthly_franchise_csv = pd.DataFrame(monthly_franchises).head(8).to_csv(index=False) if monthly_franchises else "No monthly franchise heatmap."
            global_franchise_csv = pd.DataFrame(global_franchises).head(8).to_csv(index=False) if global_franchises else "No broader franchise heatmap."
            monthly_format_csv = pd.DataFrame(monthly_formats).head(8).to_csv(index=False) if monthly_formats else "No monthly format table."
            global_format_csv = pd.DataFrame(global_formats).head(8).to_csv(index=False) if global_formats else "No broader format table."
            recent_csv = recent_five[["title", "views", "retention", "subscribers_gained", "engagement_score"]].to_csv(index=False)
            trend_csv = trend_df[["query", "title", "channel_title"]].head(8).to_csv(index=False) if trend_df is not None and not trend_df.empty else "No trend videos."
            prompt = textwrap.dedent(
                f"""
                Review this monthly momentum snapshot for {st.session_state.vault_settings.get("CHANNEL_NAME", "this channel")}.
                Keep the answer concise and strategic.
                Return:
                1. What topic or niche boomed most this month
                2. What seems to be getting traction or interaction
                3. Which archetypes or upload styles are strongest right now
                4. Three next video or cover ideas that keep the momentum going
                5. One idea that is safer and one idea that is riskier but high-upside

                Recent monthly uploads:
                {recent_csv}

                Topic traction:
                {topic_csv}

                Monthly archetypes:
                {monthly_archetype_csv}

                Broader upload archetypes:
                {global_archetype_csv}

                Monthly franchise heat:
                {monthly_franchise_csv}

                Broader franchise heat:
                {global_franchise_csv}

                Monthly upload formats:
                {monthly_format_csv}

                Broader upload formats:
                {global_format_csv}

                Related niche trend videos:
                {trend_csv}
                """
            ).strip()
            with st.chat_message("assistant"):
                st.write_stream(stream_aria_response(prompt, model))
    with right:
        if trend_df is not None and not trend_df.empty:
            trend_rows = []
            trend_preview = trend_df[["title", "channel_title"]].head(8).copy()
            for _, row in trend_preview.iterrows():
                trend_rows.append((str(row["title"])[:48], str(row["channel_title"])[:22]))
            render_leaderboard_card("Trend Watch", trend_rows, dense=False)
        elif trend_message:
            st.caption(trend_message)
