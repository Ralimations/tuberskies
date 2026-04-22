from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_ollama_response
from aria_app.pattern_memory import refresh_pattern_memory
from aria_app.ui import render_editorial_list, render_insight_card, render_panel_header, render_status_strip
from aria_app.features.command_center_parts.analytics import (
    build_channel_audit_rows,
    build_creator_hero_stats,
    build_publish_timing_table,
    build_today_desk_payload,
    build_analytics_chart,
    get_alert_rows,
    render_creator_hero,
)
from aria_app.features.command_center_parts.upload_lab import build_upload_takeaways, render_upload_lab
from aria_app.features.command_center_parts.pattern_view import render_pattern_memory
from mock_data import generate_analytics_data
from youtube_cache import (
    cached_channel_profile,
    cached_live_analytics,
    cached_video_performance,
)
from youtube_client import (
    authorize_youtube_analytics,
    has_saved_token,
)
from aria_app.features.command_center_parts.action_feed import build_action_feed_cards, render_action_feed

def render_command_center() -> None:
    force_refresh = bool(st.session_state.pop("force_youtube_cache_refresh", False))
    live_df, live_message = cached_live_analytics(st.session_state.vault_settings, force_refresh=force_refresh)
    video_df, video_message = cached_video_performance(st.session_state.vault_settings, force_refresh=force_refresh)
    live_profile, live_profile_message = (
        cached_channel_profile(st.session_state.vault_settings, force_refresh=force_refresh)
        if has_saved_token()
        else (None, "")
    )
    st.session_state.analytics_source = "Live YouTube"
    using_demo_analytics = live_df is None
    analytics_df = live_df if live_df is not None else generate_analytics_data(days=90)

    channel_name = str(live_profile.get("title", "Ralskies")) if live_profile else "Ralskies"
    channel_handle = str(live_profile.get("handle", "@ralskies")) if live_profile else "@ralskies"
    status = "Live YouTube connected" if live_df is not None else "Demo analytics until YouTube is connected"
    render_creator_hero(
        channel_name=channel_name,
        handle=channel_handle,
        summary="A quiet analytics environment for moving from channel pulse to upload-level evidence without losing the thread.",
        stats=build_creator_hero_stats(analytics_df, video_df, st.session_state.calendar_df, live_profile),
        status=status,
    )

    auth_col1, auth_col2 = st.columns([1, 1.6])
    auth_button_label = "Reconnect YouTube" if has_saved_token() else "Connect YouTube Analytics"
    if auth_col1.button(auth_button_label, key="command_center_auth"):
        try:
            st.session_state.youtube_auth_notice = authorize_youtube_analytics(st.session_state.vault_settings)
        except Exception as error:
            st.session_state.youtube_auth_notice = f"YouTube authorization failed: {error}"
    if auth_col1.button("Refresh YouTube Cache", key="command_center_refresh_cache"):
        st.session_state.force_youtube_cache_refresh = True
        st.rerun()
    if st.session_state.youtube_auth_notice:
        auth_col2.info(st.session_state.youtube_auth_notice)

    if using_demo_analytics:
        st.info(live_message or "Showing a sample creator dashboard until live YouTube analytics are connected.")
    else:
        st.success(live_message)
    if live_df is None and video_message and video_df is not None and not video_df.empty:
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

    command_sections = ["Dashboard", "Analytics", "Pattern Memory", "Upload Lab"]
    if st.session_state.get("command_center_section") == "Overview":
        st.session_state.command_center_section = "Analytics"
    if st.session_state.get("command_center_section") in {"Today Desk", "Channel Audit", "Publish Timing"}:
        st.session_state.command_center_section = "Analytics"
    if st.session_state.get("command_center_section") not in command_sections:
        st.session_state.command_center_section = "Dashboard"

    active_section = st.session_state.command_center_section

    if active_section == "Dashboard":
        feed_cards = build_action_feed_cards(
            analytics_df=analytics_df,
            video_df=video_df,
            calendar_df=st.session_state.calendar_df,
            today_payload=today_payload,
            upload_takeaways=st.session_state.upload_takeaways,
            using_demo_analytics=using_demo_analytics,
            live_message=live_message,
        )
        render_action_feed(feed_cards)
        return

    if active_section == "Analytics":
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
            render_panel_header("Analytics Drill-Down", "The report view behind the action feed: trend, audit, timing, and today's recommended move.")
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
            render_editorial_list(
                "Today Brief",
                [
                    ("Primary Focus", today_payload["focus_title"]),
                    ("Risk", today_payload["risk_title"]),
                    ("Opportunity", today_payload["opportunity_title"]),
                    ("Move", today_payload["today_action"]),
                ],
            )
            render_editorial_list("Channel Audit", audit_rows)
            if timing_df.empty:
                render_editorial_list("Best Publish Days", [("Status", "Waiting for daily analytics.")])
            else:
                top_days = timing_df.sort_values("publish_score", ascending=False).head(3)
                render_editorial_list("Best Publish Days", [(row["weekday"], f"Score {row['publish_score']:.1f}") for _, row in top_days.iterrows()])
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

    if active_section == "Pattern Memory":
        render_pattern_memory(pattern_snapshot or {})
        return

    if active_section == "Upload Lab":
        render_upload_lab(video_df if video_df is not None else pd.DataFrame(), video_message)
        return

