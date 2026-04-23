from __future__ import annotations

from datetime import date

import pandas as pd


def _next_milestone(value: int, base: int = 1_000) -> int:
    if value < base:
        return base
    digits = len(str(max(value, 1)))
    for step in (1, 2, 5, 10):
        milestone = step * (10 ** (digits - 1))
        if milestone > value:
            return milestone
    return 10 ** digits


def _milestone_meta(value: int, unit: str, base: int = 1_000) -> str:
    milestone = _next_milestone(value, base=base)
    remaining = max(milestone - value, 0)
    return f"{remaining:,} {unit} to {milestone:,}"


def build_creator_hero_stats(
    analytics_df: pd.DataFrame,
    video_df: pd.DataFrame | None,
    calendar_df: pd.DataFrame,
    live_profile: dict[str, object] | None,
) -> list[tuple[str, str, str]]:
    last_30 = analytics_df.tail(30)
    views = int(last_30["views"].fillna(0).sum()) if not last_30.empty else 0
    watch_time = int(round(last_30["watch_time_hours"].fillna(0).sum())) if not last_30.empty else 0
    subscribers = (
        f"{int(live_profile.get('subscriber_count', '0')):,}"
        if live_profile
        else f"+{int(last_30['subscribers_gained'].fillna(0).sum()):,}"
        if not last_30.empty
        else "--"
    )
    active_projects = len(calendar_df) if calendar_df is not None else 0
    upload_count = len(video_df) if video_df is not None and not video_df.empty else 0
    subscriber_value = int(live_profile.get("subscriber_count", "0")) if live_profile else int(last_30["subscribers_gained"].fillna(0).sum()) if not last_30.empty else 0
    next_pipeline = ((active_projects // 5) + 1) * 5
    return [
        ("Views", f"{views:,}", _milestone_meta(views, "views")),
        ("Subscribers", subscribers, _milestone_meta(subscriber_value, "subs", base=100)),
        ("Watch Time", f"{watch_time:,}h", _milestone_meta(watch_time, "hours", base=100)),
        ("Pipeline", str(active_projects), f"{max(next_pipeline - active_projects, 0)} more to {next_pipeline} active ideas"),
    ]


def build_analytics_chart(df: pd.DataFrame, metric_name: str) -> None:
    import plotly.express as px
    import streamlit as st

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
        template="plotly_dark",
    )
    chart.update_traces(line=dict(color="#2d7df0", width=2.4), marker=dict(size=4, color="#2d7df0"))
    chart.update_layout(
        height=380,
        margin=dict(l=18, r=18, t=52, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#151922",
        font=dict(color="#f6f7fb", family="Inter, Segoe UI, Arial, sans-serif"),
        title_font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=17, color="#f6f7fb"),
        xaxis_title=None,
        yaxis_title=None,
    )
    chart.update_xaxes(showgrid=False, linecolor="#252b37", tickfont=dict(color="#a7afbf"))
    chart.update_yaxes(gridcolor="#252b37", zeroline=False, tickfont=dict(color="#a7afbf"))
    st.plotly_chart(chart, use_container_width=True)


def get_alert_rows(df: pd.DataFrame) -> pd.DataFrame:
    ctr_alert = df["ctr"] < 5.0 if "ctr" in df.columns and df["ctr"].notna().any() else pd.Series(False, index=df.index)
    retention_alert = df["retention"] < 42.0 if "retention" in df.columns else pd.Series(False, index=df.index)
    return df[ctr_alert | retention_alert].sort_values("date", ascending=False)


def get_trend_rows(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["date", "trend", "views", "views_change", "retention", "ctr"]
    if df.empty or "views" not in df.columns:
        return pd.DataFrame(columns=columns)

    trends = df.copy().sort_values("date")
    trends["views"] = pd.to_numeric(trends["views"], errors="coerce").fillna(0)
    trends["views_change"] = trends["views"].diff().fillna(0)
    baseline = trends["views"].rolling(7, min_periods=2).mean().shift(1)
    trends["trend_strength"] = (trends["views"] - baseline).fillna(trends["views_change"])
    trends["trend"] = trends["trend_strength"].apply(lambda value: "Spike" if value > 0 else "Dip")
    top = trends.reindex(trends["trend_strength"].abs().sort_values(ascending=False).index).head(8).copy()

    for column in ["views", "views_change", "retention", "ctr"]:
        if column in top.columns:
            top[column] = pd.to_numeric(top[column], errors="coerce")
    top["views"] = top["views"].round(0).astype("Int64")
    top["views_change"] = top["views_change"].round(0).astype("Int64")
    if "retention" in top.columns:
        top["retention"] = top["retention"].round(0).astype("Int64")
    if "ctr" in top.columns:
        top["ctr"] = top["ctr"].round(0).astype("Int64")
    return top[columns].reset_index(drop=True)


def build_channel_audit_rows(df: pd.DataFrame, calendar_df: pd.DataFrame, vault_settings: dict[str, str]) -> list[tuple[str, str]]:
    if df.empty:
        return [("Live Analytics", "Not loaded yet")]

    last_30 = df.tail(30)
    retention = last_30["retention"].dropna().mean()
    views = last_30["views"].sum()
    due_soon = calendar_df["target_upload_date"].notna().sum()
    description_ready = "Yes" if vault_settings.get("default_description", "").strip() else "No"
    backlog_balance = calendar_df["stage"].value_counts().to_dict()
    editing_count = backlog_balance.get("Video Editing", 0)
    idea_count = backlog_balance.get("Song Idea", 0)

    return [
        ("Retention Health", "Strong" if pd.notna(retention) and retention >= 45 else "Needs attention"),
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
    summary["avg_views"] = summary["avg_views"].round(0).astype("Int64")
    summary["avg_retention"] = summary["avg_retention"].round(0).astype("Int64")
    summary["publish_score"] = (summary["avg_views"] * 0.5 + summary["avg_retention"] * 8 + summary["avg_watch_time"] * 4).round(0).astype("Int64")
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
