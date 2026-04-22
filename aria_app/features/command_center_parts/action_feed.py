from __future__ import annotations

from html import escape
from urllib.parse import quote, urlencode

import pandas as pd
import streamlit as st

from aria_app.features.command_center_parts.analytics import build_publish_timing_table, get_alert_rows


def _href(params: dict[str, str]) -> str:
    return f"?{urlencode(params, quote_via=quote)}"


def _clip(value: object, length: int = 96) -> str:
    text = str(value or "").strip()
    if len(text) <= length:
        return text
    return f"{text[: length - 1].rstrip()}..."


def _best_calendar_row(calendar_df: pd.DataFrame) -> pd.Series | None:
    if calendar_df is None or calendar_df.empty:
        return None

    rank_map = {"High": 0, "Medium": 1, "Low": 2}
    stage_weight = {"Upload": 0, "Video Editing": 1, "BandLab Recording": 2, "Instrumental Prep": 3, "Song Idea": 4}
    ranked = calendar_df.copy()
    ranked["priority_rank"] = ranked["priority"].map(rank_map).fillna(1)
    ranked["stage_rank"] = ranked["stage"].map(stage_weight).fillna(4)
    ranked["target_rank"] = ranked["target_upload_date"].fillna(pd.Timestamp.today().normalize() + pd.Timedelta(days=365))
    ranked = ranked.sort_values(["priority_rank", "stage_rank", "target_rank", "title"])
    return ranked.iloc[0] if not ranked.empty else None


def build_action_feed_cards(
    analytics_df: pd.DataFrame,
    video_df: pd.DataFrame | None,
    calendar_df: pd.DataFrame,
    today_payload: dict[str, str],
    upload_takeaways: dict[str, object],
    using_demo_analytics: bool,
    live_message: str,
) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []

    if using_demo_analytics:
        cards.append(
            {
                "category": "Analytics",
                "title": "Connect YouTube Analytics",
                "age": "setup",
                "body": live_message or "Live data unlocks personalized feed cards, upload history, and channel timing signals.",
                "tags": [("Live Data", "Missing"), ("Demo Mode", "On")],
                "cta": "Open Vault",
                "href": _href({"view": "The Vault"}),
            }
        )

    alerts = get_alert_rows(analytics_df).head(1) if analytics_df is not None and not analytics_df.empty else pd.DataFrame()
    if not alerts.empty:
        alert = alerts.iloc[0]
        metric_note = f"Retention {alert['retention']:.1f}%"
        if "ctr" in alert and pd.notna(alert.get("ctr")):
            metric_note = f"CTR {alert['ctr']:.1f}% | {metric_note}"
        cards.append(
            {
                "category": "Analytics",
                "title": f"Review the dip on {alert['date'].strftime('%b %d')}",
                "age": "latest signal",
                "body": f"{metric_note}. Check whether the next title, thumbnail promise, or first 20 seconds needs tightening.",
                "tags": [("Risk", "Retention"), ("Action", "Analyze")],
                "cta": "Analyze trend",
                "href": _href({"view": "Command Center", "command_center_section": "Analytics"}),
            }
        )

    focus_title = today_payload.get("focus_title", "")
    if focus_title and focus_title != "No active song selected":
        cards.append(
            {
                "category": "Production",
                "title": f"Move {focus_title} forward",
                "age": "today",
                "body": today_payload.get("focus_reason", "This is the cleanest production move for today."),
                "tags": [("Focus", "Repertoire"), ("Next Step", "Ready")],
                "cta": "Open Repertoire",
                "href": _href({"view": "Repertoire", "repertoire_section": "Idea Board"}),
            }
        )
    else:
        cards.append(
            {
                "category": "Production",
                "title": "Add one active song to the pipeline",
                "age": "setup",
                "body": "A.R.I.A. needs at least one current song or cover idea before it can rank the best next production move.",
                "tags": [("Pipeline", "Empty"), ("Action", "Add Song")],
                "cta": "Open Repertoire",
                "href": _href({"view": "Repertoire", "repertoire_section": "Idea Board"}),
            }
        )

    best = upload_takeaways.get("best") if upload_takeaways else None
    if best is not None:
        best_title = _clip(best.get("title", "Top upload"), 72)
        thumb = str(best.get("thumbnail_url", "") or "")
        cards.append(
            {
                "category": "Optimization",
                "title": "Repeat the strongest upload pattern",
                "age": "upload history",
                "body": f"{best_title} is the strongest upload in view. Use its framing as the model for the next title, hook, or cover concept.",
                "tags": [
                    ("Views", f"{int(best.get('views', 0)):,}"),
                    ("Retention", f"{float(best.get('retention', 0)):.1f}%"),
                ],
                "cta": "Review Upload Lab",
                "href": _href({"view": "Command Center", "command_center_section": "Upload Lab"}),
                "thumbnail": thumb,
            }
        )
        cards.append(
            {
                "category": "Optimization",
                "title": "Review tags and description before publishing changes",
                "age": "safe action",
                "body": f"Open Creator Actions to load the current metadata for {best_title}, draft improvements, and publish only after manual review.",
                "tags": [("Guardrail", "Review First"), ("API", "YouTube")],
                "cta": "Open Creator Actions",
                "href": _href({"view": "Creator Actions"}),
                "thumbnail": thumb,
            }
        )

    improvement_rows = upload_takeaways.get("improvement_rows", []) if upload_takeaways else []
    if improvement_rows:
        label, value = improvement_rows[0]
        cards.append(
            {
                "category": "Optimization",
                "title": f"Fix the biggest upload weakness: {label}",
                "age": "pattern",
                "body": value,
                "tags": [("Weak Spot", label), ("Action", "Package")],
                "cta": "Review history",
                "href": _href({"view": "Command Center", "command_center_section": "Upload Lab", "upload_lab_section": "Summary"}),
            }
        )

    timing_df = build_publish_timing_table(analytics_df)
    if not timing_df.empty:
        best_day = timing_df.sort_values("publish_score", ascending=False).iloc[0]
        cards.append(
            {
                "category": "Research",
                "title": f"Protect {best_day['weekday']} for a strong upload",
                "age": "timing",
                "body": f"{best_day['weekday']} currently leads the publish score at {best_day['publish_score']:.1f}. Save it for the most polished near-ready release.",
                "tags": [("Avg Views", f"{best_day['avg_views']:.0f}"), ("Retention", f"{best_day['avg_retention']:.1f}%")],
                "cta": "Open Analytics",
                "href": _href({"view": "Command Center", "command_center_section": "Analytics"}),
            }
        )

    if st.session_state.get("niche_output", "").strip():
        cards.append(
            {
                "category": "Research",
                "title": "Turn the latest Niche Lab output into a concrete upload",
                "age": "fresh idea",
                "body": _clip(st.session_state.niche_output.strip().splitlines()[0], 140),
                "tags": [("Idea", "Generated"), ("Action", "Package")],
                "cta": "Open Niche Lab",
                "href": _href({"view": "Niche Lab"}),
            }
        )

    if video_df is not None and not video_df.empty and "comment_count" in video_df.columns:
        comment_total = int(video_df["comment_count"].fillna(0).sum())
        if comment_total > 0:
            cards.append(
                {
                    "category": "Production",
                    "title": "Reply to recent comments safely",
                    "age": "community",
                    "body": f"Your loaded upload window has {comment_total:,} comments. Draft warm replies, then post one at a time from Creator Actions.",
                    "tags": [("Replies", "Manual"), ("Bulk", "Disabled")],
                    "cta": "Open Comment Inbox",
                    "href": _href({"view": "Creator Actions"}),
                }
            )
    else:
        cards.append(
            {
                "category": "Research",
                "title": "Extract fan-request signals",
                "age": "idea source",
                "body": "Paste comments or Ko-fi requests so A.R.I.A. can detect repeated songs, artists, and high-retention request themes.",
                "tags": [("Requests", "Ready"), ("Source", "Comments")],
                    "cta": "Open Ideation",
                    "href": _href({"view": "Niche Lab"}),
            }
        )

    priority_row = _best_calendar_row(calendar_df)
    if priority_row is not None and str(priority_row.get("stage", "")) in {"Upload", "Video Editing", "BandLab Recording"}:
        cards.append(
            {
                "category": "Shorts",
                "title": "Turn the next performance into Shorts",
                "age": "repurpose",
                "body": f"{priority_row.get('title', 'Your next release')} is far enough along to prepare vertical clips or captions.",
                "tags": [("Format", "Shorts"), ("Stage", priority_row.get("stage", "Active"))],
                "cta": "Open Shorts Architect",
                "href": _href({"view": "Shorts Architect", "shorts_section": "Ingest"}),
            }
        )
    else:
        cards.append(
            {
                "category": "Shorts",
                "title": "Queue a performance for Shorts clipping",
                "age": "repurpose",
                "body": "Upload a long-form performance when ready, then let A.R.I.A. detect high-energy moments and build captioned vertical exports.",
                "tags": [("Format", "9:16"), ("Captions", "Whisper")],
                "cta": "Open Shorts Architect",
                "href": _href({"view": "Shorts Architect", "shorts_section": "Ingest"}),
            }
        )

    return cards[:9]


def render_action_feed(cards: list[dict[str, object]]) -> None:
    categories = ["All", "Optimization", "Research", "Analytics", "Production", "Shorts"]
    active_filter = st.segmented_control(
        "Action feed filter",
        options=categories,
        default="All",
        key="action_feed_filter",
        label_visibility="collapsed",
    )
    filtered_cards = [card for card in cards if active_filter == "All" or card["category"] == active_filter]
    insight_count = len(cards)
    st.markdown(
        f'<div class="feed-alert"><span></span><strong>{insight_count} action{"s" if insight_count != 1 else ""} ready for you</strong></div>',
        unsafe_allow_html=True,
    )

    if not filtered_cards:
        st.info("No feed cards match this filter yet.")
        return

    for card in filtered_cards:
        tags = "".join(
            f'<span><b>{escape(str(label))}</b>{escape(str(value))}</span>'
            for label, value in card.get("tags", [])
        )
        thumbnail = escape(str(card.get("thumbnail", "") or ""))
        thumbnail_markup = f'<img class="feed-thumb" src="{thumbnail}" alt="">' if thumbnail else '<div class="feed-thumb feed-thumb-empty"></div>'
        markup = (
            '<div class="feed-card">'
            '<div class="feed-card-top">'
            f'<div><h3>{escape(str(card["title"]))}</h3><p>{escape(str(card["body"]))}</p></div>'
            f'<span class="feed-age">{escape(str(card["age"]))}</span>'
            '</div>'
            '<div class="feed-card-body">'
            f'{thumbnail_markup}'
            f'<div class="feed-card-meta"><div class="feed-card-tags">{tags}</div>'
            f'<a class="feed-card-button" href="{escape(str(card["href"]))}" target="_self">{escape(str(card["cta"]))}</a></div>'
            '</div>'
            '</div>'
        )
        st.markdown(markup, unsafe_allow_html=True)
