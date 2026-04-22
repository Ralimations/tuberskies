from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st

from aria_app.ai import stream_ollama_response
from aria_app.pattern_memory import refresh_pattern_memory
from aria_app.ui import render_action_strip, render_editorial_list, render_insight_card, render_panel_header, render_status_strip
from aria_app.features.command_center_parts.analytics import (
    build_channel_audit_rows,
    build_creator_hero_stats,
    build_publish_timing_table,
    build_today_desk_payload,
    build_analytics_chart,
    get_alert_rows,
    render_creator_hero,
    render_dashboard_snapshot,
)
from aria_app.features.command_center_parts.upload_lab import build_upload_takeaways, render_upload_lab
from aria_app.features.command_center_parts.pattern_view import render_pattern_memory
from mock_data import generate_analytics_data
from youtube_client import (
    authorize_youtube_analytics,
    get_live_channel_profile,
    has_saved_token,
    load_live_analytics,
    load_video_performance,
)

def render_command_center() -> None:
    live_df, live_message = load_live_analytics(st.session_state.vault_settings)
    video_df, video_message = load_video_performance(st.session_state.vault_settings)
    live_profile, live_profile_message = get_live_channel_profile(st.session_state.vault_settings) if has_saved_token() else (None, "")
    st.session_state.analytics_source = "Live YouTube"
    using_demo_analytics = live_df is None
    analytics_df = live_df if live_df is not None else generate_analytics_data(days=90)

    channel_name = str(live_profile.get("title", "Ralskies")) if live_profile else "Ralskies"
    channel_handle = str(live_profile.get("handle", "@ralskies")) if live_profile else "@ralskies"
    status = "Live YouTube connected" if live_df is not None else "Demo analytics until YouTube is connected"
    render_creator_hero(
        channel_name=channel_name,
        handle=channel_handle,
        summary="A creator-driven studio for deciding what to record, when to publish, which formats are working, and where A.R.I.A. should focus next.",
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

    render_action_strip(
        "Creator Control Strip",
        "Start with the dashboard, then move into analytics, audit, timing, memory, or upload-level decisions.",
        ["Dashboard", "Analytics", "Uploads", "Pipeline"],
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

    command_sections = ["Dashboard", "Today Desk", "Analytics", "Channel Audit", "Publish Timing", "Pattern Memory", "Upload Lab"]
    if st.session_state.get("command_center_section") == "Overview":
        st.session_state.command_center_section = "Analytics"
    if st.session_state.get("command_center_section") not in command_sections:
        st.session_state.command_center_section = "Dashboard"

    st.markdown('<div class="subnav-wrap">', unsafe_allow_html=True)
    active_section = st.segmented_control(
        "Command Center Section",
        options=command_sections,
        default="Dashboard",
        key="command_center_section",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if active_section == "Dashboard":
        render_dashboard_snapshot(analytics_df, video_df, st.session_state.calendar_df)
        return

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
