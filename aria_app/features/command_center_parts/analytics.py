from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from aria_app.ui import (
    render_creator_hero,
    render_editorial_list,
    render_insight_card,
    render_leaderboard_card,
    render_panel_header,
    render_stat_card,
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
    return [
        ("Views", f"{views:,}", "last 30 days"),
        ("Subscribers", subscribers, "channel total or recent gain"),
        ("Watch Time", f"{watch_time:,}h", "last 30 days"),
        ("Pipeline", str(active_projects), f"{upload_count} uploads tracked"),
    ]


def render_dashboard_snapshot(analytics_df: pd.DataFrame, video_df: pd.DataFrame | None, calendar_df: pd.DataFrame) -> None:
    render_panel_header(
        "Macro Pulse",
        "A broad read on channel health, audience response, upload performance, and production pressure before any drill-down.",
    )
    build_metric_row(analytics_df)
    build_health_snapshot(analytics_df)

    left, center, right = st.columns([1.25, 0.95, 0.9])
    with left:
        build_analytics_chart(analytics_df, "views")
    with center:
        if video_df is not None and not video_df.empty:
            upload_rows = []
            for _, row in video_df.head(6).iterrows():
                upload_rows.append((str(row["title"])[:44], f"{int(row['views']):,} views"))
            render_leaderboard_card("Top Uploads", upload_rows, dense=False)
        else:
            render_leaderboard_card(
                "Top Uploads",
                [("Connect YouTube Analytics", "upload data"), ("Then return here", "ranked history")],
                dense=False,
            )
        alerts = get_alert_rows(analytics_df).head(4)
        render_editorial_list(
            "Signal Alerts",
            [
                (
                    row["date"].strftime("%Y-%m-%d"),
                    f"Retention {row['retention']:.1f}%",
                )
                for _, row in alerts.iterrows()
            ]
            or [("Status", "No major retention alerts in the current view.")],
        )
    with right:
        stage_counts = calendar_df["stage"].value_counts().to_dict() if calendar_df is not None and not calendar_df.empty else {}
        render_editorial_list(
            "Production Pipeline",
            [
                ("Ideas", str(stage_counts.get("Song Idea", 0))),
                ("Prep", str(stage_counts.get("Instrumental Prep", 0))),
                ("Recording", str(stage_counts.get("BandLab Recording", 0))),
                ("Editing", str(stage_counts.get("Video Editing", 0))),
                ("Upload Ready", str(stage_counts.get("Upload", 0))),
            ],
        )
        timing_df = build_publish_timing_table(analytics_df)
        if timing_df.empty:
            render_editorial_list("Best Publish Days", [("Status", "Waiting for daily analytics.")])
        else:
            top_days = timing_df.sort_values("publish_score", ascending=False).head(3)
            render_editorial_list("Best Publish Days", [(row["weekday"], f"Score {row['publish_score']:.1f}") for _, row in top_days.iterrows()])


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
    chart.update_traces(line=dict(color="#176b87", width=2.4), marker=dict(size=4, color="#176b87"))
    chart.update_layout(
        height=380,
        margin=dict(l=18, r=18, t=52, b=18),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#141516", family="Inter, Segoe UI, Arial, sans-serif"),
        title_font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=17, color="#141516"),
        xaxis_title=None,
        yaxis_title=None,
    )
    chart.update_xaxes(showgrid=False, linecolor="#dedfda", tickfont=dict(color="#6b706f"))
    chart.update_yaxes(gridcolor="#ecece7", zeroline=False, tickfont=dict(color="#6b706f"))
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
