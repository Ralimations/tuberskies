from __future__ import annotations

import re
import textwrap
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from aria_app.ai import stream_ollama_response
from aria_app.pattern_memory import refresh_pattern_memory
from aria_app.ui import (
    render_action_strip,
    render_editorial_list,
    render_insight_card,
    render_leaderboard_card,
    render_panel_header,
    render_section_header,
    render_stat_card,
    render_status_strip,
)
from youtube_client import (
    authorize_youtube_analytics,
    get_live_channel_profile,
    has_saved_token,
    load_live_analytics,
    load_video_performance,
    search_music_trends,
)


def build_metric_row(df: pd.DataFrame) -> None:
    if df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            render_stat_card("Views | Last 30 Days", "--", "Waiting for live YouTube data")
        with col2:
            render_stat_card("Subscribers | Last 30 Days", "--", "Waiting for live YouTube data")
        with col3:
            render_stat_card("Watch Time | Last 30 Days", "--", "Waiting for live YouTube data")
        return

    last_30 = df.tail(30)
    views = int(last_30["views"].fillna(0).sum())
    subscribers = int(last_30["subscribers_gained"].fillna(0).sum())
    watch_time_hours = int(round(last_30["watch_time_hours"].fillna(0).sum()))
    col1, col2, col3 = st.columns(3)
    with col1:
        render_stat_card("Views | Last 30 Days", f"{views:,}", "Rolling total from live channel analytics")
    with col2:
        render_stat_card("Subscribers | Last 30 Days", f"{subscribers:,}", "Subscribers gained across the last 30 days")
    with col3:
        render_stat_card("Watch Time | Last 30 Days", f"{watch_time_hours:,}", "Estimated watch time hours from live analytics")


def build_health_snapshot(df: pd.DataFrame) -> None:
    latest = df.tail(7)
    previous = df.tail(14).head(7)
    if latest.empty or previous.empty:
        return

    has_ctr = df["ctr"].notna().any()
    ctr_delta = latest["ctr"].mean() - previous["ctr"].mean() if has_ctr else None
    retention_delta = latest["retention"].mean() - previous["retention"].mean()
    views_delta = latest["views"].sum() - previous["views"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        if has_ctr:
            render_insight_card("CTR Momentum", f"{latest['ctr'].mean():.2f}%", f"{ctr_delta:+.2f} pts versus the previous 7-day window.")
        else:
            render_insight_card("CTR Momentum", "Unavailable", "CTR is not returned by the current live YouTube Analytics query.")
    with col2:
        render_insight_card("Retention Momentum", f"{latest['retention'].mean():.2f}%", f"{retention_delta:+.2f} pts versus the previous 7-day window.")
    with col3:
        render_insight_card("Views Momentum", f"{latest['views'].sum():,}", f"{views_delta:+,} views compared with the previous 7 days.")


def build_analytics_chart(df: pd.DataFrame, metric_name: str) -> None:
    if df.empty or metric_name not in df.columns:
        st.info("No live analytics are available for this chart yet.")
        return

    chart_df = df.dropna(subset=[metric_name]).copy()
    if chart_df.empty:
        st.info(f"{metric_name.upper() if metric_name == 'ctr' else metric_name.title()} is not available from the current live analytics query.")
        return

    labels = {"ctr": "CTR (%)", "retention": "Retention (%)", "views": "Views"}
    chart = px.line(
        chart_df,
        x="date",
        y=metric_name,
        markers=True,
        title=f"{labels[metric_name]} Over Time",
        template="plotly_white",
    )
    chart.update_traces(line=dict(color="#4DB8FF", width=3), marker=dict(size=6, color="#FFD700"))
    chart.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,34,53,0.65)",
        font=dict(color="#edf2ff", family="Inter, Segoe UI, sans-serif"),
        title_font=dict(family="Montserrat, Bahnschrift, sans-serif", size=22),
        xaxis_title=None,
        yaxis_title=None,
    )
    chart.update_xaxes(showgrid=False)
    chart.update_yaxes(gridcolor="rgba(237,242,255,0.08)")
    st.plotly_chart(chart, use_container_width=True)


def get_alert_rows(df: pd.DataFrame) -> pd.DataFrame:
    ctr_alert = df["ctr"] < 5.0 if "ctr" in df.columns and df["ctr"].notna().any() else pd.Series(False, index=df.index)
    retention_alert = df["retention"] < 42.0 if "retention" in df.columns else pd.Series(False, index=df.index)
    return df[ctr_alert | retention_alert].sort_values("date", ascending=False)


def build_channel_audit_rows(df: pd.DataFrame, calendar_df: pd.DataFrame, vault_settings: dict[str, str]) -> list[tuple[str, str]]:
    if df.empty:
        return [("Live Analytics", "Not loaded yet")]

    last_30 = df.tail(30)
    retention = last_30["retention"].mean()
    views = last_30["views"].sum()
    due_soon = calendar_df["target_upload_date"].notna().sum()
    description_ready = "Yes" if vault_settings.get("default_description", "").strip() else "No"
    backlog_balance = calendar_df["stage"].value_counts().to_dict()
    editing_count = backlog_balance.get("Video Editing", 0)
    idea_count = backlog_balance.get("Song Idea", 0)

    return [
        ("Retention Health", "Strong" if retention >= 45 else "Needs attention"),
        ("30 Day Demand", f"{int(views):,} views"),
        ("Description Template", description_ready),
        ("Ideas in Queue", str(idea_count)),
        ("Editing Load", str(editing_count)),
        ("Scheduled Items", str(due_soon)),
    ]


def build_publish_timing_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["weekday", "avg_views", "avg_retention", "publish_score"])

    timing_df = df.copy()
    timing_df["weekday"] = timing_df["date"].dt.day_name()
    summary = (
        timing_df.groupby("weekday", dropna=False)
        .agg(avg_views=("views", "mean"), avg_retention=("retention", "mean"), avg_watch_time=("watch_time_hours", "mean"))
        .reset_index()
    )
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    summary["weekday"] = pd.Categorical(summary["weekday"], categories=weekday_order, ordered=True)
    summary = summary.sort_values("weekday")
    summary["publish_score"] = (summary["avg_views"] * 0.5 + summary["avg_retention"] * 8 + summary["avg_watch_time"] * 4).round(1)
    return summary[["weekday", "avg_views", "avg_retention", "publish_score"]]


def build_today_desk_payload(analytics_df: pd.DataFrame, calendar_df: pd.DataFrame, niche_output: str) -> dict[str, str]:
    payload = {
        "focus_title": "No active song selected",
        "focus_reason": "Add or update items in Repertoire so A.R.I.A. can rank the best next move.",
        "risk_title": "No live analytics warning",
        "risk_reason": "Live channel data has not raised a major issue yet.",
        "opportunity_title": "No immediate opportunity",
        "opportunity_reason": "Add a working concept or request in Niche Lab to surface stronger opportunities.",
        "today_action": "Open Repertoire and push one song one stage closer to upload.",
    }

    if not calendar_df.empty:
        rank_map = {"High": 0, "Medium": 1, "Low": 2}
        stage_weight = {"Upload": 0, "Video Editing": 1, "BandLab Recording": 2, "Instrumental Prep": 3, "Song Idea": 4}
        ranked = calendar_df.copy()
        ranked["priority_rank"] = ranked["priority"].map(rank_map).fillna(1)
        ranked["stage_rank"] = ranked["stage"].map(stage_weight).fillna(4)
        ranked["target_rank"] = ranked["target_upload_date"].fillna(pd.Timestamp(date.today()) + pd.Timedelta(days=365))
        ranked = ranked.sort_values(["priority_rank", "stage_rank", "target_rank", "title"])
        best_row = ranked.iloc[0]
        target_label = best_row["target_upload_date"].strftime("%Y-%m-%d") if pd.notna(best_row["target_upload_date"]) else "no deadline yet"
        payload["focus_title"] = best_row["title"] or "Untitled song"
        payload["focus_reason"] = f"{best_row['priority']} priority in {best_row['stage']}, with target {target_label}. This is the cleanest next push for momentum."
        payload["today_action"] = f"Move '{best_row['title'] or 'this song'}' forward from {best_row['stage']} today."

    if not analytics_df.empty:
        alerts = get_alert_rows(analytics_df)
        if not alerts.empty:
            top_alert = alerts.iloc[0]
            metric_note = (
                f"CTR {top_alert['ctr']:.2f}% and retention {top_alert['retention']:.2f}%"
                if pd.notna(top_alert["ctr"])
                else f"Retention {top_alert['retention']:.2f}%"
            )
            payload["risk_title"] = f"Performance dip on {top_alert['date'].strftime('%Y-%m-%d')}"
            payload["risk_reason"] = f"Most recent warning day shows {metric_note}. This is the clearest place to review packaging or pacing."
        else:
            latest = analytics_df.tail(7)
            if not latest.empty:
                payload["risk_title"] = "No urgent analytics fires"
                payload["risk_reason"] = f"Recent retention averages {latest['retention'].mean():.2f}%. A.R.I.A. can focus on growth moves instead of damage control."

        timing_df = build_publish_timing_table(analytics_df)
        if not timing_df.empty:
            best_day = timing_df.sort_values("publish_score", ascending=False).iloc[0]
            payload["opportunity_title"] = f"Best publish window: {best_day['weekday']}"
            payload["opportunity_reason"] = f"This weekday currently leads your local timing score at {best_day['publish_score']:.1f}. Use it for your strongest near-ready upload."

    if niche_output.strip():
        payload["opportunity_title"] = "Niche Lab has a fresh lead"
        payload["opportunity_reason"] = niche_output.strip().splitlines()[0][:120]

    if payload["risk_title"] != "No live analytics warning" and "review packaging or pacing" in payload["risk_reason"]:
        payload["today_action"] = "Review the weakest live analytics day, then tighten the next title, thumbnail framing, or intro pacing."

    return payload


def extract_keyword_candidates(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "your", "into", "then", "than",
        "male", "version", "cover", "song", "video", "a", "an", "of", "to", "in", "on", "or",
    }
    filtered = [word for word in words if len(word) > 2 and word not in stop_words]
    unique_words = list(dict.fromkeys(filtered))
    phrases: list[str] = []
    for size in (2, 3):
        for index in range(len(filtered) - size + 1):
            phrase = " ".join(filtered[index : index + size])
            if phrase not in phrases:
                phrases.append(phrase)
    return unique_words[:8] + phrases[:8]


def build_keyword_opportunity_df(topic: str, working_title: str, calendar_df: pd.DataFrame) -> pd.DataFrame:
    source_text = f"{topic} {working_title}".strip()
    if not source_text:
        return pd.DataFrame(columns=["keyword", "demand", "competition", "channel_fit", "score"])
    candidates = extract_keyword_candidates(source_text)
    channel_context = " ".join(calendar_df["content_pillar"].fillna("").astype(str).tolist()).lower()
    notes_context = " ".join(calendar_df["notes"].fillna("").astype(str).tolist()).lower()
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        word_count = len(candidate.split())
        candidate_lower = candidate.lower()
        demand = min(10, 5 + word_count + (2 if any(term in candidate_lower for term in ["broadway", "hazbin", "epic", "disney"]) else 0))
        competition = max(1, 10 - word_count * 2 - (2 if "male version" in source_text.lower() or "reimagined" in source_text.lower() else 0))
        fit = 4
        if candidate_lower in channel_context:
            fit += 3
        if candidate_lower in notes_context:
            fit += 2
        if any(term in candidate_lower for term in ["theatrical", "ballad", "dreamy", "broadway", "male", "reimagined"]):
            fit += 2
        fit = min(10, fit)
        score = round(demand * 0.35 + (11 - competition) * 0.25 + fit * 0.4, 1)
        rows.append({"keyword": candidate, "demand": demand, "competition": competition, "channel_fit": fit, "score": score})
    frame = pd.DataFrame(rows).drop_duplicates(subset=["keyword"]).sort_values(["score", "channel_fit"], ascending=False)
    return frame.head(10).reset_index(drop=True)


def build_title_scorecard(title: str, topic: str) -> list[tuple[str, str]]:
    if not title.strip():
        return [("Title Score", "Add a working title to score packaging strength")]
    lowered_title = title.lower()
    title_length = len(title.strip())
    contains_keyword = any(keyword in lowered_title for keyword in extract_keyword_candidates(topic)[:5]) if topic.strip() else False
    emotional_language = any(term in lowered_title for term in ["male version", "reimagined", "broadway", "emotional", "ballad", "dramatic", "live"])
    concise = 35 <= title_length <= 70
    score = 0
    score += 3 if concise else 1
    score += 3 if contains_keyword else 1
    score += 3 if emotional_language else 1
    score += 1 if any(symbol in title for symbol in ["(", ")", "|", ":"]) else 0
    return [
        ("Packaging Score", f"{score}/10"),
        ("Length", "Strong" if concise else f"{title_length} chars"),
        ("Primary Keyword", "Present" if contains_keyword else "Weak"),
        ("Emotion / Framing", "Strong" if emotional_language else "Needs a hook"),
    ]


def build_upload_takeaways(video_df: pd.DataFrame) -> dict[str, object]:
    empty_result: dict[str, object] = {
        "best": None,
        "weak": None,
        "pattern_rows": [],
        "improvement_rows": [],
    }
    if video_df is None or video_df.empty:
        return empty_result

    ranked = video_df.sort_values(["engagement_score", "views"], ascending=False).reset_index(drop=True)
    best = ranked.iloc[0]
    weak = ranked.iloc[-1]

    top_slice = ranked.head(min(8, len(ranked)))
    lower_slice = ranked.tail(min(8, len(ranked)))

    top_titles = " ".join(top_slice["title"].fillna("").astype(str).tolist()).lower()
    low_titles = " ".join(lower_slice["title"].fillna("").astype(str).tolist()).lower()

    pattern_rows: list[tuple[str, str]] = []
    improvement_rows: list[tuple[str, str]] = []

    if "male version" in top_titles:
        pattern_rows.append(("Packaging", "Male-version framing shows up in stronger uploads."))
    if "cover" in top_titles or "reimagined" in top_titles:
        pattern_rows.append(("Format", "Reimagined or cover framing appears in stronger uploads."))
    if top_slice["retention"].mean() >= lower_slice["retention"].mean():
        pattern_rows.append(("Retention", f"Top uploads average {top_slice['retention'].mean():.1f}% retention."))
    if top_slice["subscribers_gained"].fillna(0).sum() > 0:
        pattern_rows.append(("Subscriber Pull", f"Top uploads gained {int(top_slice['subscribers_gained'].fillna(0).sum())} subscribers in this window."))

    if lower_slice["retention"].mean() < top_slice["retention"].mean():
        improvement_rows.append(("Retention Gap", f"Lower performers trail by {(top_slice['retention'].mean() - lower_slice['retention'].mean()):.1f} retention points."))
    if lower_slice["watch_time_hours"].mean() < top_slice["watch_time_hours"].mean():
        improvement_rows.append(("Watch Time", "Weaker uploads hold less total watch time, which suggests less replay or weaker completion."))
    if "official audio" in low_titles:
        improvement_rows.append(("Packaging", "Plain utility-style titles look weaker than emotional or theatrical framing."))
    improvement_rows.append(("Next Move", "Model future titles on the best upload's framing, then test a sharper opening on the next release."))

    return {
        "best": best,
        "weak": weak,
        "pattern_rows": pattern_rows[:4],
        "improvement_rows": improvement_rows[:4],
    }


def assign_archetype_labels(title: str) -> list[str]:
    lowered = str(title).lower()
    labels: list[str] = []

    keyword_map = {
        "Hazbin": ["hazbin", "angel dust", "husk", "gravity"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Male Version": ["male version", "male cover"],
        "English Version": ["english version", "english ver", "english ver."],
        "Original": ["into the stars", "dreaming", "original song", "original music"],
        "Short-form Teaser": ["coming soon", "#shorts", "#viral"],
        "Cover": ["cover", "reimagined"],
        "Collaboration": ["ft.", "feat.", "with "],
        "Live / Session": ["live", "session", "acoustic"],
    }

    for label, keywords in keyword_map.items():
        if any(keyword in lowered for keyword in keywords):
            labels.append(label)

    if not labels:
        labels.append("General Performance")

    return labels


def _days_since_published(published_at: pd.Timestamp) -> int:
    if pd.isna(published_at):
        return 365
    published = pd.to_datetime(published_at, errors="coerce")
    if pd.isna(published):
        return 365
    if getattr(published, "tzinfo", None) is not None:
        published = published.tz_localize(None)
    today = pd.Timestamp(date.today())
    return max(int((today - published.normalize()).days), 0)


def assign_format_labels(title: str) -> list[str]:
    lowered = str(title).lower()
    labels: list[str] = []

    if any(keyword in lowered for keyword in ["coming soon", "#shorts", "#viral", "teaser", "snippet", "preview"]):
        labels.append("Short-form / Teaser")
    if any(keyword in lowered for keyword in ["ft.", "feat.", "with "]):
        labels.append("Collab Format")
    if any(keyword in lowered for keyword in ["live", "session", "acoustic"]):
        labels.append("Live Format")
    if any(keyword in lowered for keyword in ["cover", "reimagined", "english version", "male version"]):
        labels.append("Produced Cover")
    if "original" in lowered or any(keyword in lowered for keyword in ["into the stars", "dreaming"]):
        labels.append("Original Release")

    if not labels:
        labels.append("Standard Upload")

    return labels


def assign_franchise_label(title: str) -> str:
    lowered = str(title).lower()
    franchise_map = {
        "Hazbin Hotel": ["hazbin", "angel dust", "husk", "gravity", "losing streak", "brighter"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Original Universe": ["into the stars", "dreaming", "original"],
    }
    for label, keywords in franchise_map.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return "General / Mixed"


def build_archetype_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        labels = assign_archetype_labels(row.get("title", ""))
        for label in labels:
            grouped.setdefault(label, []).append(
                {
                    "views": float(row.get("views", 0) or 0),
                    "retention": float(row.get("retention", 0) or 0),
                    "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                    "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                    "engagement_score": float(row.get("engagement_score", 0) or 0),
                }
            )

    rows: list[dict[str, object]] = []
    for label, items in grouped.items():
        frame = pd.DataFrame(items)
        upload_count = len(frame)
        avg_views = frame["views"].mean()
        avg_retention = frame["retention"].mean()
        avg_watch_time = frame["watch_time_hours"].mean()
        total_subscribers = frame["subscribers_gained"].sum()
        avg_score = frame["engagement_score"].mean()
        momentum_score = round(float(avg_views * 0.35 + avg_retention * 10 + avg_watch_time * 2.5 + total_subscribers * 6 + avg_score * 0.15), 1)
        rows.append(
            {
                "archetype": label,
                "uploads": upload_count,
                "avg_views": round(float(avg_views), 1),
                "avg_retention": round(float(avg_retention), 2),
                "avg_watch_time_hours": round(float(avg_watch_time), 1),
                "total_subscribers": int(total_subscribers),
                "avg_engagement_score": round(float(avg_score), 1),
                "momentum_score": momentum_score,
            }
        )

    rows.sort(key=lambda row: (row["momentum_score"], row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_format_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        for label in assign_format_labels(row.get("title", "")):
            grouped.setdefault(label, []).append(
                {
                    "views": float(row.get("views", 0) or 0),
                    "retention": float(row.get("retention", 0) or 0),
                    "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                    "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                    "engagement_score": float(row.get("engagement_score", 0) or 0),
                }
            )

    rows: list[dict[str, object]] = []
    for label, items in grouped.items():
        frame = pd.DataFrame(items)
        rows.append(
            {
                "format": label,
                "uploads": int(len(frame)),
                "avg_views": round(float(frame["views"].mean()), 1),
                "avg_retention": round(float(frame["retention"].mean()), 2),
                "avg_engagement_score": round(float(frame["engagement_score"].mean()), 1),
                "total_subscribers": int(frame["subscribers_gained"].sum()),
            }
        )

    rows.sort(key=lambda row: (row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_franchise_heatmap_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        franchise = assign_franchise_label(row.get("title", ""))
        days_old = _days_since_published(row.get("published_at"))
        recency_weight = max(0.3, 1.35 - min(days_old, 365) / 365)
        grouped.setdefault(franchise, []).append(
            {
                "views": float(row.get("views", 0) or 0),
                "retention": float(row.get("retention", 0) or 0),
                "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                "engagement_score": float(row.get("engagement_score", 0) or 0),
                "recency_weight": float(recency_weight),
            }
        )

    rows: list[dict[str, object]] = []
    for franchise, items in grouped.items():
        frame = pd.DataFrame(items)
        weighted_score = (
            (
                frame["views"] * 0.25
                + frame["retention"] * 12
                + frame["watch_time_hours"] * 2
                + frame["subscribers_gained"] * 8
                + frame["engagement_score"] * 0.18
            )
            * frame["recency_weight"]
        ).mean()
        rows.append(
            {
                "franchise": franchise,
                "uploads": int(len(frame)),
                "avg_views": round(float(frame["views"].mean()), 1),
                "avg_retention": round(float(frame["retention"].mean()), 2),
                "avg_engagement_score": round(float(frame["engagement_score"].mean()), 1),
                "recent_heat": round(float(weighted_score), 1),
                "recent_bias": round(float(frame["recency_weight"].mean()), 2),
                "total_subscribers": int(frame["subscribers_gained"].sum()),
            }
        )

    rows.sort(key=lambda row: (row["recent_heat"], row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_archetype_recommendations(month_rows: list[dict[str, object]], global_rows: list[dict[str, object]]) -> list[tuple[str, str]]:
    recommendations: list[tuple[str, str]] = []

    if month_rows:
        top_month = month_rows[0]
        recommendations.append(
            (
                "Current Winner",
                f"{top_month['archetype']} is the strongest current lane with momentum score {top_month['momentum_score']:.1f}.",
            )
        )

    if global_rows:
        top_global = global_rows[0]
        recommendations.append(
            (
                "Reliable Across Window",
                f"{top_global['archetype']} looks strongest across the broader upload history, not just this month.",
            )
        )

    month_labels = {row["archetype"] for row in month_rows[:4]}
    global_labels = {row["archetype"] for row in global_rows[:4]}
    overlap = [label for label in month_labels if label in global_labels]
    if overlap:
        recommendations.append(
            (
                "Repeatable Lane",
                f"{overlap[0]} is showing both short-term and broader strength, which makes it a safer momentum play.",
            )
        )

    if month_rows:
        high_retention = sorted(month_rows, key=lambda row: row["avg_retention"], reverse=True)[0]
        if high_retention["archetype"] != month_rows[0]["archetype"]:
            recommendations.append(
                (
                    "High-Retention Wildcard",
                    f"{high_retention['archetype']} keeps viewers well. It could be a strong creative pivot if packaged better.",
                )
            )

    return recommendations[:4]


def build_heatmap_recommendations(
    franchise_rows: list[dict[str, object]],
    format_rows: list[dict[str, object]],
) -> list[tuple[str, str]]:
    recommendations: list[tuple[str, str]] = []

    if franchise_rows:
        hottest = franchise_rows[0]
        recommendations.append(
            (
                "Hottest Franchise",
                f"{hottest['franchise']} is carrying the strongest recent heat at {hottest['recent_heat']:.1f}.",
            )
        )

    if len(franchise_rows) > 1:
        runner_up = franchise_rows[1]
        recommendations.append(
            (
                "Second Best Bet",
                f"{runner_up['franchise']} is the next-closest momentum lane and worth keeping warm.",
            )
        )

    if format_rows:
        best_format = format_rows[0]
        recommendations.append(
            (
                "Best Format",
                f"{best_format['format']} currently looks strongest by engagement and views.",
            )
        )

    high_retention_franchise = None
    if franchise_rows:
        high_retention_franchise = sorted(franchise_rows, key=lambda row: row["avg_retention"], reverse=True)[0]
    if high_retention_franchise and high_retention_franchise["franchise"] != franchise_rows[0]["franchise"]:
        recommendations.append(
            (
                "Retention Wildcard",
                f"{high_retention_franchise['franchise']} holds attention especially well and may deserve better packaging.",
            )
        )

    return recommendations[:4]


def build_request_signal_rows(request_text: str) -> list[dict[str, object]]:
    if not request_text.strip():
        return []

    request_patterns = {
        "Hazbin Hotel": ["hazbin", "angel dust", "husk", "gravity", "losing streak", "brighter"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Male Version": ["male version", "male cover"],
        "English Version": ["english version", "english ver", "english"],
        "Original": ["original", "into the stars", "dreaming"],
    }

    lowered = request_text.lower()
    rows: list[dict[str, object]] = []
    for label, keywords in request_patterns.items():
        count = sum(lowered.count(keyword) for keyword in keywords)
        if count > 0:
            rows.append({"signal": label, "mentions": count})

    rows.sort(key=lambda row: row["mentions"], reverse=True)
    return rows


def build_gap_rows(monthly_df: pd.DataFrame, global_franchises: list[dict[str, object]]) -> list[dict[str, object]]:
    if not global_franchises:
        return []

    month_titles = " ".join(monthly_df["title"].fillna("").astype(str).tolist()).lower() if monthly_df is not None and not monthly_df.empty else ""
    rows: list[dict[str, object]] = []
    for row in global_franchises[:6]:
        franchise = str(row["franchise"])
        if franchise == "Hazbin Hotel":
            active = "hazbin" in month_titles
        elif franchise == "Epic / Ilium":
            active = any(keyword in month_titles for keyword in ["epic", "ilium", "troy", "fire"])
        elif franchise == "K-Pop Demon Hunters":
            active = any(keyword in month_titles for keyword in ["kpop demon hunters", "saja boys", "your idol", "soda pop"])
        elif franchise == "Original Universe":
            active = any(keyword in month_titles for keyword in ["into the stars", "dreaming", "original"])
        else:
            active = True

        if not active:
            rows.append(
                {
                    "franchise": franchise,
                    "recent_heat": row["recent_heat"],
                    "gap_note": f"{franchise} is strong in the broader window but missing from the selected month.",
                }
            )

    rows.sort(key=lambda row: row["recent_heat"], reverse=True)
    return rows


def build_next_cover_radar(
    monthly_df: pd.DataFrame,
    monthly_franchises: list[dict[str, object]],
    global_franchises: list[dict[str, object]],
    monthly_formats: list[dict[str, object]],
    trend_df: pd.DataFrame | None,
    niche_output: str,
) -> list[dict[str, object]]:
    radar_rows: list[dict[str, object]] = []
    request_rows = build_request_signal_rows(niche_output)
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

    if request_rows:
        top_request = request_rows[0]
        radar_rows.append(
            {
                "lane": "Fan Signal Play",
                "franchise": top_request["signal"],
                "format": "Produced Cover",
                "confidence": "Medium",
                "idea": franchise_idea_map.get(top_request["signal"], "a fan-requested performance idea"),
                "why": f"Request memory currently points to {top_request['signal']} with {top_request['mentions']} detected mentions.",
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
        "A.R.I.A.'s recommendation layer. It combines franchise heat, format strength, recent upload gaps, niche trends, and fan-request signals into concrete next-move options.",
    )

    radar_rows = build_next_cover_radar(
        monthly_df=monthly_df,
        monthly_franchises=monthly_franchises,
        global_franchises=global_franchises,
        monthly_formats=monthly_formats,
        trend_df=trend_df,
        niche_output=st.session_state.niche_output,
    )
    request_rows = build_request_signal_rows(st.session_state.niche_output)
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
            "Fan Request Signals",
            [(row["signal"], f"{row['mentions']} mention(s)") for row in request_rows] or [("Status", "No fan request signals have been detected yet.")],
        )
        render_editorial_list(
            "Opportunity Gaps",
            [(row["franchise"], row["gap_note"]) for row in gap_rows[:4]] or [("Status", "No major franchise gap detected this month.")],
        )

    if st.button("Ask A.R.I.A. for the Best Next Cover", key="next_cover_radar_coach"):
        model = st.session_state.vault_settings.get("ollama_model", "gemma")
        radar_csv = pd.DataFrame(radar_rows).to_csv(index=False)
        request_csv = pd.DataFrame(request_rows).to_csv(index=False) if request_rows else "No request signals."
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

            Fan request signals:
            {request_csv}

            Opportunity gaps:
            {gap_csv}

            Related trend videos:
            {trend_csv}
            """
        ).strip()
        with st.chat_message("assistant"):
            st.write_stream(stream_ollama_response(prompt, model))


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
            ideas.append(("Trend-adjacent option", f"Consider a Ralskies spin on: {title}"))

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
    trend_df, trend_message = search_music_trends(settings, trend_queries) if trend_queries else (None, "No trend queries available yet.")
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

    st.markdown('<div class="subnav-wrap">', unsafe_allow_html=True)
    momentum_section = st.segmented_control(
        "Momentum Workspace",
        options=["Snapshot", "Scoreboards", "Trend Watch"],
        default="Snapshot",
        key="momentum_workspace_section",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

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
                Review this monthly momentum snapshot for Ralskies.
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
                st.write_stream(stream_ollama_response(prompt, model))
    with right:
        if trend_df is not None and not trend_df.empty:
            trend_rows = []
            trend_preview = trend_df[["title", "channel_title"]].head(8).copy()
            for _, row in trend_preview.iterrows():
                trend_rows.append((str(row["title"])[:48], str(row["channel_title"])[:22]))
            render_leaderboard_card("Trend Watch", trend_rows, dense=False)
        elif trend_message:
            st.caption(trend_message)


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

    st.markdown('<div class="subnav-wrap">', unsafe_allow_html=True)
    upload_section = st.segmented_control(
        "Upload Lab Section",
        options=["Summary", "History", "Momentum", "Radar"],
        default="Summary",
        key="upload_lab_section",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
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
                    st.write_stream(stream_ollama_response(prompt, model))
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
    trend_df, _ = search_music_trends(st.session_state.vault_settings, trend_queries) if trend_queries else (None, "No trend queries")
    render_next_cover_radar(
        monthly_df=monthly_df,
        monthly_franchises=build_franchise_heatmap_rows(monthly_df) if not monthly_df.empty else [],
        global_franchises=build_franchise_heatmap_rows(video_df),
        monthly_formats=build_format_rows(monthly_df) if not monthly_df.empty else [],
        trend_df=trend_df,
    )


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


def render_command_center() -> None:
    render_section_header("Performance", "Command Center", "Track discovery, retention, and audience response for theatrical covers, reimagined performances, and original releases.")

    live_df, live_message = load_live_analytics(st.session_state.vault_settings)
    video_df, video_message = load_video_performance(st.session_state.vault_settings)
    live_profile, live_profile_message = get_live_channel_profile(st.session_state.vault_settings) if has_saved_token() else (None, "")
    st.session_state.analytics_source = "Live YouTube"
    analytics_df = live_df if live_df is not None else pd.DataFrame(columns=["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"])

    auth_col1, auth_col2 = st.columns([1, 1.6])
    auth_button_label = "Reconnect YouTube" if has_saved_token() else "Connect YouTube Analytics"
    if auth_col1.button(auth_button_label, key="command_center_auth"):
        try:
            st.session_state.youtube_auth_notice = authorize_youtube_analytics(st.session_state.vault_settings)
        except Exception as error:
            st.session_state.youtube_auth_notice = f"YouTube authorization failed: {error}"
    if st.session_state.youtube_auth_notice:
        auth_col2.info(st.session_state.youtube_auth_notice)

    if live_df is None and (video_df is None or video_df.empty):
        st.error(live_message or video_message or "No live YouTube data is available yet.")
        return

    if live_df is not None:
        st.success(live_message)
    elif video_message:
        st.warning(f"Daily analytics are unavailable right now. {video_message}")

    if live_profile:
        render_status_strip(
            [
                ("Connected Channel", live_profile.get("title", "YouTube Channel")),
                ("Subscribers", f"{int(live_profile.get('subscriber_count', '0')):,}"),
                ("Videos", f"{int(live_profile.get('video_count', '0')):,}"),
            ]
        )
    elif live_profile_message:
        st.caption(live_profile_message)

    build_metric_row(analytics_df)
    build_health_snapshot(analytics_df)
    render_action_strip(
        "Daily Control Strip",
        "Stay in one pane at a time: monitor live channel health, inspect upload history, or jump straight into momentum planning.",
        ["Live YouTube", "Upload Lab", "Pattern Memory"],
    )
    st.session_state.upload_takeaways = build_upload_takeaways(video_df if video_df is not None else pd.DataFrame())
    st.session_state.pattern_memory = refresh_pattern_memory(
        analytics_df,
        st.session_state.calendar_df,
        st.session_state.niche_output,
    )
    pattern_snapshot = st.session_state.pattern_memory.get("latest")

    today_payload = build_today_desk_payload(analytics_df, st.session_state.calendar_df, st.session_state.niche_output)
    audit_rows = build_channel_audit_rows(analytics_df, st.session_state.calendar_df, st.session_state.vault_settings)
    timing_df = build_publish_timing_table(analytics_df)

    metric_options = ["views", "retention"]
    if analytics_df["ctr"].notna().any():
        metric_options.insert(0, "ctr")

    st.markdown('<div class="subnav-wrap">', unsafe_allow_html=True)
    active_section = st.segmented_control(
        "Command Center Section",
        options=["Today Desk", "Overview", "Channel Audit", "Publish Timing", "Pattern Memory", "Upload Lab"],
        default="Today Desk",
        key="command_center_section",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if active_section == "Today Desk":
        render_panel_header("Today Desk", "The one-screen daily brief. This is where A.R.I.A. should feel better than generic creator tools: less noise, clearer action.")
        row1, row2 = st.columns([1.15, 0.85])
        with row1:
            render_insight_card("Best Next Focus", today_payload["focus_title"], today_payload["focus_reason"])
            render_insight_card("Biggest Current Risk", today_payload["risk_title"], today_payload["risk_reason"])
        with row2:
            render_insight_card("Best Opportunity", today_payload["opportunity_title"], today_payload["opportunity_reason"])
            render_insight_card("Recommended Move Today", "Do This Next", today_payload["today_action"])
        render_editorial_list(
            "Daily Checklist",
            [
                ("Primary Focus", today_payload["focus_title"]),
                ("Analytics Check", today_payload["risk_title"]),
                ("Growth Angle", today_payload["opportunity_title"]),
                ("Action", today_payload["today_action"]),
            ],
        )
        if st.button("Ask A.R.I.A. for Today's Brief", key="today_desk_brief"):
            model = st.session_state.vault_settings.get("ollama_model", "gemma")
            prompt = textwrap.dedent(
                f"""
                Build a short daily operating brief for Ralskies.
                Keep it practical and brief.

                Best next focus: {today_payload["focus_title"]}
                Focus reason: {today_payload["focus_reason"]}
                Biggest current risk: {today_payload["risk_title"]}
                Risk detail: {today_payload["risk_reason"]}
                Best opportunity: {today_payload["opportunity_title"]}
                Opportunity detail: {today_payload["opportunity_reason"]}
                Recommended move today: {today_payload["today_action"]}
                """
            ).strip()
            with st.chat_message("assistant"):
                response = st.write_stream(stream_ollama_response(prompt, model))
            st.session_state.calendar_coach_output = response or ""
            st.session_state.calendar_coach_context = "A.R.I.A. Today Desk"
        return

    if active_section == "Overview":
        selected_metric = st.radio(
            "Chart focus",
            options=metric_options,
            format_func=lambda value: value.upper() if value == "ctr" else value.title(),
            horizontal=True,
            key="command_center_metric",
        )
        left, right = st.columns([1.5, 1])
        with left:
            build_analytics_chart(analytics_df, selected_metric)
        with right:
            render_panel_header("Signal Desk", "A tighter read on what A.R.I.A. should pay attention to before you ask for analysis.")
            latest_rows = analytics_df.tail(5).copy()
            latest_rows["date"] = latest_rows["date"].dt.strftime("%Y-%m-%d")
            render_editorial_list(
                "Latest Trend Read",
                [(row["date"], f'{row[selected_metric]:,.2f}' if selected_metric != "views" else f'{int(row[selected_metric]):,}') for _, row in latest_rows.iterrows()],
            )
            alerts = get_alert_rows(analytics_df).head(5)
            if alerts.empty:
                st.success("No major live-data alerts right now.")
            else:
                st.warning("Potential weak spots detected in recent performance.")
                alert_rows = []
                for _, row in alerts.iterrows():
                    alert_rows.append(
                        (
                            row["date"].strftime("%Y-%m-%d"),
                            f"CTR {row['ctr']:.2f}% | Retention {row['retention']:.2f}%" if pd.notna(row["ctr"]) else f"Retention {row['retention']:.2f}%",
                        )
                    )
                render_editorial_list("Recent Alert Days", alert_rows)
            if st.button("Analyze with A.R.I.A.", key="command_center_coach"):
                model = st.session_state.vault_settings.get("ollama_model", "gemma")
                sample = analytics_df[["date", selected_metric]].tail(14).to_csv(index=False)
                prompt = textwrap.dedent(
                    f"""
                    Review this Ralskies performance trend and explain what may be happening.
                    Focus on practical actions for the next upload cycle.

                    Metric: {selected_metric}
                    Data:
                    {sample}
                    """
                ).strip()
                with st.chat_message("assistant"):
                    st.write_stream(stream_ollama_response(prompt, model))
        return

    if active_section == "Channel Audit":
        render_panel_header("Channel Audit", "A local-first audit board inspired by vidIQ and TubeBuddy scorecards, focused on the signals A.R.I.A. can actually measure.")
        render_editorial_list("Audit Checklist", audit_rows)
        low_retention_days = analytics_df[analytics_df["retention"] < 42].tail(5)
        if low_retention_days.empty:
            st.success("Retention is not flagging any major weak days right now.")
        else:
            st.dataframe(low_retention_days[["date", "views", "retention", "watch_time_hours"]], use_container_width=True, hide_index=True)
        return

    if active_section == "Pattern Memory":
        render_pattern_memory(pattern_snapshot or {})
        return

    if active_section == "Upload Lab":
        render_upload_lab(video_df if video_df is not None else pd.DataFrame(), video_message)
        return

    render_panel_header("Publish Timing", "A lightweight best-time view inspired by creator tools that rank posting windows from recent channel performance.")
    if timing_df.empty:
        st.info("Not enough live data is available yet to rank publish timing.")
    else:
        st.dataframe(
            timing_df.assign(avg_views=timing_df["avg_views"].round(0).astype(int), avg_retention=timing_df["avg_retention"].round(2)),
            use_container_width=True,
            hide_index=True,
        )
        top_days = timing_df.sort_values("publish_score", ascending=False).head(3)
        render_editorial_list("Recommended Days", [(row["weekday"], f"Score {row['publish_score']:.1f}") for _, row in top_days.iterrows()])
