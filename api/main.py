from __future__ import annotations

import textwrap
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import ollama
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aria_app.ai import build_coach_prompt
from aria_app.features.command_center_parts.analytics import (
    build_channel_audit_rows,
    build_creator_hero_stats,
    build_publish_timing_table,
    build_today_desk_payload,
    get_alert_rows,
)
from aria_app.features.command_center_parts.keyword_tools import build_keyword_opportunity_df, build_title_scorecard
from aria_app.features.command_center_parts.upload_metrics import build_upload_takeaways
from aria_app.pattern_memory import refresh_pattern_memory
from mock_data import generate_analytics_data
from storage import PRIORITIES, STAGES, list_api_cache_rows, load_calendar, load_vault_settings, save_calendar, save_vault_settings
from youtube_cache import (
    cached_channel_profile,
    cached_comment_threads,
    cached_live_analytics,
    cached_owned_video_metadata,
    cached_video_performance,
    save_cached_owned_video_metadata,
)
from youtube_client import (
    authorize_youtube_analytics,
    clear_youtube_token,
    get_connection_status,
    has_saved_token,
    reply_to_comment,
    update_owned_video_metadata,
)


app = FastAPI(title="A.R.I.A. Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


CHAT_SUGGESTIONS = [
    "What should I do next today?",
    "Which upload pattern should I repeat?",
    "What is the biggest risk in my analytics?",
    "What should I turn into Shorts?",
]

SIDEBAR_ITEMS = [
    {"label": "Ask A.R.I.A.", "path": "/", "icon": "comments", "group": "Home"},
    {"label": "Analytics", "path": "/analytics", "icon": "chart", "group": "Home"},
    {"label": "Creator Actions", "path": "/creator-actions", "icon": "reply", "group": "Home"},
    {"label": "Upload Lab", "path": "/upload-lab", "icon": "upload", "group": "More tools"},
    {"label": "Pattern Memory", "path": "/pattern-memory", "icon": "memory", "group": "More tools"},
    {"label": "Ideation", "path": "/ideation", "icon": "spark", "group": "More tools"},
    {"label": "Repertoire", "path": "/repertoire", "icon": "music", "group": "More tools"},
    {"label": "Shorts Architect", "path": "/shorts", "icon": "scissors", "group": "More tools"},
    {"label": "The Vault", "path": "/vault", "icon": "vault", "group": "More tools"},
]

CACHE_DATASETS = {
    "youtube:channel_profile": "Channel Profile",
    "youtube:live_analytics:90": "Analytics",
    "youtube:video_performance:365:100": "Upload Performance",
    "youtube:music_trends:": "Music Trends",
    "youtube:video_metadata:": "Video Metadata",
    "youtube:comment_threads:": "Comments",
}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class IdeationRequest(BaseModel):
    topic: str = ""
    working_title: str = ""
    action: str = "title_pack"
    fan_request: str = ""
    comment_dump: str = ""


class VaultSettingsRequest(BaseModel):
    default_description: str = ""
    youtube_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    ollama_model: str = "gemma"


class CalendarRow(BaseModel):
    title: str = ""
    stage: str = STAGES[0]
    priority: str = "Medium"
    content_pillar: str = ""
    target_upload_date: str | None = None
    notes: str = ""


class CalendarSaveRequest(BaseModel):
    rows: list[CalendarRow]


class CoachRequest(BaseModel):
    prompt: str


class MetadataDraftRequest(BaseModel):
    video_label: str


class MetadataLoadRequest(BaseModel):
    video_id: str


class MetadataPublishRequest(BaseModel):
    video_id: str
    title: str
    description: str
    tags: list[str]
    reviewed: bool = False


class CommentListRequest(BaseModel):
    video_id: str = ""


class CommentDraftRequest(BaseModel):
    author: str
    text: str


class CommentPublishRequest(BaseModel):
    comment_id: str
    reply_text: str
    reviewed: bool = False


ACTION_LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "creator_action_log.jsonl"


def _log_action(action: str, payload: dict[str, object]) -> None:
    ACTION_LOG_PATH.parent.mkdir(exist_ok=True)
    row = {"created_at": datetime.now().isoformat(timespec="seconds"), "action": action, "payload": payload}
    with ACTION_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _split_tags(raw_tags: str) -> list[str]:
    cleaned = raw_tags.replace("\n", ",")
    return [tag.strip().strip("#") for tag in cleaned.split(",") if tag.strip().strip("#")]


def _video_options(video_df: pd.DataFrame | None) -> list[dict[str, str]]:
    if video_df is None or video_df.empty:
        return []
    options: list[dict[str, str]] = []
    for _, row in video_df.head(50).iterrows():
        video_id = str(row.get("video_id", "")).strip()
        title = str(row.get("title", "Untitled Video")).strip()
        if video_id:
            options.append({"label": f"{title[:72]} | {video_id}", "video_id": video_id, "title": title})
    return options


def _build_react_action_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    analytics_df = payload["analytics_df"]
    video_df = payload["video_df"]
    calendar_df = payload["calendar_df"]
    today_payload = payload["today_payload"]
    upload_takeaways = payload["upload_takeaways"]
    cards: list[dict[str, Any]] = []

    alerts = get_alert_rows(analytics_df).head(1) if analytics_df is not None and not analytics_df.empty else pd.DataFrame()
    if not alerts.empty:
        alert = alerts.iloc[0]
        metric_note = f"Retention {float(alert.get('retention', 0)):.1f}%"
        if "ctr" in alert and pd.notna(alert.get("ctr")):
            metric_note = f"CTR {float(alert.get('ctr', 0)):.1f}% | {metric_note}"
        cards.append(
            {
                "category": "Analytics",
                "title": f"Review the dip on {alert['date'].strftime('%b %d')}",
                "body": f"{metric_note}. Check whether the next title, thumbnail promise, or first 20 seconds needs tightening.",
                "cta": "Ask A.R.I.A. about this risk",
                "path": "/",
            }
        )

    focus_title = today_payload.get("focus_title", "")
    cards.append(
        {
            "category": "Production",
            "title": f"Move {focus_title} forward" if focus_title and focus_title != "No active song selected" else "Add one active song to the pipeline",
            "body": today_payload.get("focus_reason", "A.R.I.A. needs one current song before it can rank the best production move."),
            "cta": "Open Repertoire",
            "path": "/repertoire",
        }
    )

    best = upload_takeaways.get("best") if upload_takeaways else None
    if best is not None:
        title = str(best.get("title", "Top upload"))
        cards.append(
            {
                "category": "Optimization",
                "title": "Repeat the strongest upload pattern",
                "body": f"{title[:90]} is the strongest upload in view. Use its framing as the model for the next title, hook, or cover concept.",
                "cta": "Open Upload Lab",
                "path": "/upload-lab",
            }
        )

    timing_df = build_publish_timing_table(analytics_df)
    if not timing_df.empty:
        best_day = timing_df.sort_values("publish_score", ascending=False).iloc[0]
        cards.append(
            {
                "category": "Research",
                "title": f"Protect {best_day['weekday']} for a strong upload",
                "body": f"{best_day['weekday']} leads the publish score at {float(best_day['publish_score']):.1f}. Save it for the most polished near-ready release.",
                "cta": "Review publish timing",
                "path": "/analytics",
            }
        )

    if video_df is not None and not video_df.empty and "comment_count" in video_df.columns:
        comment_total = int(video_df["comment_count"].fillna(0).sum())
        if comment_total > 0:
            cards.append(
                {
                    "category": "Community",
                    "title": "Reply to recent comments safely",
                    "body": f"The loaded upload window has {comment_total:,} comments. Draft warm replies, then post one at a time.",
                    "cta": "Open Creator Actions",
                    "path": "/creator-actions",
                }
            )

    if calendar_df is not None and not calendar_df.empty:
        active = calendar_df[calendar_df["stage"].isin(["Upload", "Video Editing", "BandLab Recording"])]
        if not active.empty:
            row = active.iloc[0]
            cards.append(
                {
                    "category": "Shorts",
                    "title": "Turn the next performance into Shorts",
                    "body": f"{row.get('title', 'Your next release')} is far enough along to prepare vertical clips or captions.",
                    "cta": "Open Shorts Architect",
                    "path": "/shorts",
                }
            )

    return cards[:6]


def _calendar_rows_to_frame(rows: list[CalendarRow]) -> pd.DataFrame:
    frame = pd.DataFrame([row.model_dump() for row in rows])
    if frame.empty:
        frame = pd.DataFrame(columns=["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"])
    for column in ["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"]:
        if column not in frame.columns:
            frame[column] = ""
    frame["title"] = frame["title"].fillna("").astype(str)
    frame["stage"] = frame["stage"].where(frame["stage"].isin(STAGES), STAGES[0])
    frame["priority"] = frame["priority"].where(frame["priority"].isin(PRIORITIES), "Medium")
    frame["content_pillar"] = frame["content_pillar"].fillna("").astype(str)
    frame["notes"] = frame["notes"].fillna("").astype(str)
    frame["target_upload_date"] = pd.to_datetime(frame["target_upload_date"], errors="coerce")
    return frame[["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"]]


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json_safe(item) for item in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return _json_safe(value.to_dict())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if pd.isna(value) if not isinstance(value, list | tuple | dict) else False:
        return None
    return value


def _cache_label(cache_key: str) -> str:
    for prefix, label in CACHE_DATASETS.items():
        if cache_key.startswith(prefix):
            return label
    return cache_key


def _payload_kind(row: dict[str, Any] | None) -> str:
    payload = row.get("payload") if row else None
    if isinstance(payload, dict):
        return str(payload.get("kind", "unknown"))
    return "missing"


def _build_cache_freshness_rows() -> list[dict[str, str]]:
    today = date.today().isoformat()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in list_api_cache_rows("youtube:"):
        grouped.setdefault(str(row["cache_key"]), []).append(row)

    freshness_rows: list[dict[str, str]] = []
    for cache_key, rows in grouped.items():
        today_row = next((row for row in rows if row["cache_date"] == today), None)
        latest_data_row = next((row for row in rows if _payload_kind(row) != "refresh_error"), None)
        active_row = today_row or latest_data_row or rows[0]
        today_kind = _payload_kind(today_row)
        latest_kind = _payload_kind(latest_data_row)
        if today_kind == "refresh_error":
            status = "Refresh failed today"
        elif today_row is not None and today_kind != "missing":
            status = "Fresh today"
        elif latest_data_row is not None:
            status = "Using stored data"
        else:
            status = "No stored data"

        freshness_rows.append(
            {
                "dataset": _cache_label(cache_key),
                "cache_key": cache_key,
                "status": status,
                "today_date": today_row["cache_date"] if today_row else "",
                "latest_data_date": latest_data_row["cache_date"] if latest_data_row else "",
                "payload_kind": today_kind if today_row else latest_kind,
                "updated_at": str(active_row.get("updated_at", "")),
                "message": str(active_row.get("message", "")),
            }
        )

    label_order = {label: index for index, label in enumerate(CACHE_DATASETS.values())}
    freshness_rows.sort(key=lambda row: (label_order.get(row["dataset"], 99), row["cache_key"]))
    return freshness_rows


def _load_context() -> dict[str, Any]:
    settings = load_vault_settings()
    calendar_df = load_calendar()
    live_df, live_message = cached_live_analytics(settings)
    video_df, video_message = cached_video_performance(settings)
    live_profile, profile_message = (
        cached_channel_profile(settings)
        if has_saved_token()
        else (None, "")
    )

    analytics_df = live_df if live_df is not None else generate_analytics_data(days=90)
    upload_takeaways = build_upload_takeaways(video_df if video_df is not None else pd.DataFrame())
    pattern_memory = refresh_pattern_memory(analytics_df, calendar_df, "")
    today_payload = build_today_desk_payload(analytics_df, calendar_df, "")
    profile = live_profile or {"title": "Ralskies", "handle": "@ralskies"}
    source = "Live YouTube" if live_df is not None else "Demo analytics"

    return {
        "settings": settings,
        "analytics_df": analytics_df,
        "video_df": video_df if video_df is not None else pd.DataFrame(),
        "calendar_df": calendar_df,
        "profile": profile,
        "source": source,
        "messages": {
            "analytics": live_message,
            "videos": video_message,
            "profile": profile_message,
        },
        "upload_takeaways": upload_takeaways,
        "pattern_memory": pattern_memory,
        "today_payload": today_payload,
    }


def _preview_frame(frame: pd.DataFrame, columns: list[str], rows: int = 8) -> str:
    if frame is None or frame.empty:
        return "No rows available."
    available_columns = [column for column in columns if column in frame.columns]
    if not available_columns:
        return "No matching columns available."
    return frame[available_columns].head(rows).to_csv(index=False)


def _chat_context(payload: dict[str, Any]) -> str:
    analytics_df = payload["analytics_df"]
    video_df = payload["video_df"]
    calendar_df = payload["calendar_df"]
    today_payload = payload["today_payload"]
    upload_takeaways = payload["upload_takeaways"]
    pattern_snapshot = payload["pattern_memory"].get("latest")

    last_30 = analytics_df.tail(30) if analytics_df is not None else pd.DataFrame()
    views_30 = int(last_30["views"].fillna(0).sum()) if not last_30.empty and "views" in last_30 else 0
    watch_hours_30 = float(last_30["watch_time_hours"].fillna(0).sum()) if not last_30.empty and "watch_time_hours" in last_30 else 0
    best = upload_takeaways.get("best")
    weak = upload_takeaways.get("weak")

    return textwrap.dedent(
        f"""
        Current Ralskies analytics context:
        - Data source: {payload["source"]}
        - Last 30 days views: {views_30:,}
        - Last 30 days watch time hours: {watch_hours_30:.1f}
        - Today focus: {today_payload.get("focus_title", "unknown")}
        - Today risk: {today_payload.get("risk_title", "unknown")} | {today_payload.get("risk_reason", "")}
        - Today opportunity: {today_payload.get("opportunity_title", "unknown")} | {today_payload.get("opportunity_reason", "")}
        - Best upload: {best.to_dict() if hasattr(best, "to_dict") else best}
        - Weakest upload: {weak.to_dict() if hasattr(weak, "to_dict") else weak}
        - Pattern memory snapshot: {pattern_snapshot or {}}

        Recent daily analytics:
        {_preview_frame(analytics_df.tail(14), ["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"], 14)}

        Top uploads:
        {_preview_frame(video_df, ["title", "views", "retention", "watch_time_hours", "subscribers_gained", "comment_count", "engagement_score"], 8)}

        Repertoire:
        {_preview_frame(calendar_df, ["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"], 10)}
        """
    ).strip()


def _build_chat_prompt(message: str, history: list[ChatMessage], context: str) -> str:
    recent_chat = "\n".join(f"{item.role}: {item.content}" for item in history[-8:])
    return textwrap.dedent(
        f"""
        You are A.R.I.A. answering as if the creator is chatting directly with their analytics.
        Be concrete, brief, and action-oriented. If data is demo, cached, missing, or uncertain, say so plainly.
        If the creator is only greeting you, testing the chat, thanking you, or making small talk, respond naturally in one short sentence and do not give analytics recommendations yet.
        Only give analytics recommendations when the creator asks for advice, analysis, decisions, risks, patterns, uploads, Shorts, metadata, comments, or next actions.

        Analytics context:
        {context}

        Recent chat:
        {recent_chat or "No prior chat in this session."}

        Creator question:
        {message}
        """
    ).strip()


def _small_talk_response(message: str) -> str | None:
    cleaned = " ".join(message.lower().strip().replace("!", "").replace(".", "").split())
    greetings = {"hi", "hello", "hey", "yo", "sup", "test", "testing"}
    thanks = {"thanks", "thank you", "ty"}
    if cleaned in greetings:
        return "Hey. I am here and ready to read the channel with you."
    if cleaned in thanks:
        return "Anytime. Send me the next question when you want to dig in."
    if cleaned in {"who are you", "what are you"}:
        return "I am A.R.I.A., your local channel analytics and creator strategy assistant."
    return None


def _assistant_response(prompt: str, model: str) -> str:
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are A.R.I.A., a concise private YouTube analytics strategist for Ralskies.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return str(response.get("message", {}).get("content", "")).strip()
    except Exception as error:  # pragma: no cover
        return f"Local Ollama request failed: {error}"


def _stream_assistant_response(prompt: str, model: str):
    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are A.R.I.A., a concise private YouTube analytics strategist for Ralskies.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as error:  # pragma: no cover
        yield f"Local Ollama request failed: {error}"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/bootstrap")
def bootstrap() -> dict[str, Any]:
    payload = _load_context()
    analytics_df = payload["analytics_df"]
    video_df = payload["video_df"]
    profile = payload["profile"]
    calendar_df = payload["calendar_df"]
    stats = build_creator_hero_stats(analytics_df, video_df, calendar_df, profile if profile else None)
    analytics_rows = analytics_df.tail(30).copy()
    if "date" in analytics_rows.columns:
        analytics_rows["date"] = pd.to_datetime(analytics_rows["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    return _json_safe(
        {
            "navigation": SIDEBAR_ITEMS,
            "chatSuggestions": CHAT_SUGGESTIONS,
            "profile": {
                "title": profile.get("title", "Ralskies"),
                "handle": profile.get("handle", "@ralskies"),
                "source": payload["source"],
            },
            "stats": [{"label": label, "value": value, "meta": meta} for label, value, meta in stats],
            "today": payload["today_payload"],
            "uploadTakeaways": payload["upload_takeaways"],
            "patternMemory": payload["pattern_memory"].get("latest"),
            "analyticsRows": analytics_rows,
            "videoRows": video_df.head(20),
            "calendarRows": calendar_df,
            "messages": payload["messages"],
        }
    )


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    small_talk = _small_talk_response(request.message)
    if small_talk:
        return {"role": "assistant", "content": small_talk}
    payload = _load_context()
    prompt = _build_chat_prompt(request.message, request.history, _chat_context(payload))
    model = payload["settings"].get("ollama_model", "gemma")
    response = _assistant_response(prompt, model)
    if not response:
        response = "I could not produce a response from the local model. Check Ollama, then try again."
    return {"role": "assistant", "content": response}


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    small_talk = _small_talk_response(request.message)
    if small_talk:
        return StreamingResponse(iter([small_talk]), media_type="text/plain")
    payload = _load_context()
    prompt = _build_chat_prompt(request.message, request.history, _chat_context(payload))
    model = payload["settings"].get("ollama_model", "gemma")
    return StreamingResponse(_stream_assistant_response(prompt, model), media_type="text/plain")


@app.post("/api/ideation/generate")
def generate_ideation(request: IdeationRequest) -> dict[str, str]:
    payload = _load_context()
    action = request.action
    if action == "extract_requests":
        prompt = textwrap.dedent(
            f"""
            Review the pasted YouTube comments for Ralskies and extract likely fan song requests.
            Return:
            1. A deduplicated list of requested songs or artists
            2. The most repeated request themes
            3. Which request seems strongest for retention potential
            4. One suggested 'Ralskies spin' for the top request

            Comments:
            {request.comment_dump}
            """
        ).strip()
    elif action == "fan_request_spin":
        prompt = build_coach_prompt(request.fan_request or request.topic, request.working_title, "fan_request_spin")
    else:
        prompt = build_coach_prompt(request.topic, request.working_title, action)
    response = _assistant_response(prompt, payload["settings"].get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not generate an ideation response."}


@app.post("/api/ideation/score")
def score_ideation(request: IdeationRequest) -> dict[str, Any]:
    calendar_df = load_calendar()
    keywords = build_keyword_opportunity_df(request.topic, request.working_title, calendar_df)
    scorecard = build_title_scorecard(request.working_title, request.topic)
    return _json_safe(
        {
            "keywords": keywords,
            "scorecard": [{"label": label, "value": value} for label, value in scorecard],
        }
    )


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    payload = _load_context()
    analytics_df = payload["analytics_df"]
    calendar_df = payload["calendar_df"]
    video_df = payload["video_df"]
    analytics_rows = analytics_df.tail(45).copy()
    alert_rows = get_alert_rows(analytics_df).head(8).copy()
    timing_df = build_publish_timing_table(analytics_df)
    audit_rows = build_channel_audit_rows(analytics_df, calendar_df, payload["settings"])

    for frame in (analytics_rows, alert_rows):
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    return _json_safe(
        {
            "source": payload["source"],
            "profile": payload["profile"],
            "stats": [
                {"label": label, "value": value, "meta": meta}
                for label, value, meta in build_creator_hero_stats(analytics_df, video_df, calendar_df, payload["profile"])
            ],
            "today": payload["today_payload"],
            "rows": analytics_rows,
            "alerts": alert_rows,
            "publishTiming": timing_df,
            "auditRows": [{"label": label, "value": value} for label, value in audit_rows],
            "actionCards": _build_react_action_cards(payload),
            "messages": payload["messages"],
        }
    )


@app.get("/api/vault")
def vault() -> dict[str, Any]:
    settings = load_vault_settings()
    status = get_connection_status(settings)
    return {
        "settings": settings,
        "connection": {
            "api_key": bool(settings.get("youtube_api_key", "").strip()),
            "oauth_client": bool(settings.get("youtube_client_id", "").strip() and settings.get("youtube_client_secret", "").strip()),
            "token": has_saved_token(),
            "connected": status.connected,
            "message": status.message,
        },
        "cache": _build_cache_freshness_rows(),
    }


@app.post("/api/vault")
def save_vault(request: VaultSettingsRequest) -> dict[str, Any]:
    save_vault_settings(
        {
            "DEFAULT_DESCRIPTION": request.default_description,
            "YOUTUBE_API_KEY": request.youtube_api_key,
            "YOUTUBE_CLIENT_ID": request.youtube_client_id,
            "YOUTUBE_CLIENT_SECRET": request.youtube_client_secret,
            "OLLAMA_MODEL": request.ollama_model,
        }
    )
    return vault()


@app.post("/api/vault/youtube/clear-token")
def clear_youtube_authorization() -> dict[str, Any]:
    clear_youtube_token()
    payload = vault()
    payload["message"] = "The saved local YouTube token was removed. Reconnect YouTube before checking fresh data."
    return payload


@app.post("/api/vault/youtube/authorize")
def authorize_youtube() -> dict[str, Any]:
    message = authorize_youtube_analytics(load_vault_settings())
    payload = vault()
    payload["message"] = message
    return payload


@app.post("/api/vault/youtube/check-latest")
def check_latest_youtube_data() -> dict[str, Any]:
    settings = load_vault_settings()
    live_df, live_message = cached_live_analytics(settings, force_refresh=True)
    video_df, video_message = cached_video_performance(settings, force_refresh=True)
    profile, profile_message = (
        cached_channel_profile(settings, force_refresh=True)
        if has_saved_token()
        else (None, "No saved YouTube token is available. Reconnect YouTube first.")
    )
    return _json_safe(
        {
            "success": live_df is not None or video_df is not None or profile is not None,
            "messages": {
                "analytics": live_message,
                "videos": video_message,
                "profile": profile_message,
            },
            "profile": profile,
            "cache": _build_cache_freshness_rows(),
        }
    )


@app.get("/api/repertoire")
def repertoire() -> dict[str, Any]:
    frame = load_calendar()
    stage_counts = frame["stage"].value_counts().reindex(STAGES, fill_value=0).to_dict()
    due_soon = frame[
        frame["target_upload_date"].notna()
        & (frame["target_upload_date"] <= pd.Timestamp.today().normalize() + pd.Timedelta(days=14))
    ]
    return _json_safe(
        {
            "rows": frame,
            "stages": STAGES,
            "priorities": PRIORITIES,
            "summary": {
                "total": len(frame),
                "ready": int(stage_counts.get("Upload", 0)),
                "due_soon": len(due_soon),
                "stage_counts": stage_counts,
            },
        }
    )


@app.post("/api/repertoire")
def save_repertoire(request: CalendarSaveRequest) -> dict[str, Any]:
    save_calendar(_calendar_rows_to_frame(request.rows))
    return repertoire()


@app.post("/api/repertoire/coach")
def coach_repertoire(request: CoachRequest) -> dict[str, str]:
    settings = load_vault_settings()
    response = _assistant_response(request.prompt, settings.get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not produce repertoire feedback."}


@app.get("/api/creator-actions")
def creator_actions() -> dict[str, Any]:
    settings = load_vault_settings()
    video_df, video_message = cached_video_performance(settings)
    return _json_safe(
        {
            "videos": _video_options(video_df),
            "message": video_message,
            "guardrails": [
                ("No autopilot", "A.R.I.A. drafts only; you approve each publish."),
                ("No bulk replies", "Replies are sent one comment at a time."),
                ("No duplicate spam", "Already-replied threads are flagged before posting."),
                ("Official API", "Uses YouTube OAuth, not browser automation."),
            ],
        }
    )


@app.post("/api/creator-actions/metadata/load")
def load_metadata(request: MetadataLoadRequest) -> dict[str, Any]:
    metadata, message = cached_owned_video_metadata(load_vault_settings(), request.video_id)
    return _json_safe({"metadata": metadata, "message": message})


@app.post("/api/creator-actions/metadata/draft")
def draft_metadata(request: MetadataDraftRequest) -> dict[str, str]:
    payload = _load_context()
    prompt = textwrap.dedent(
        f"""
        Draft safer YouTube metadata improvements for this Ralskies video.
        Return a concise result with:
        1. A refined description opening
        2. A comma-separated tag list under 450 total characters
        3. One caution if the current title should not be changed

        Current video: {request.video_label}
        Current local pattern memory: {payload["pattern_memory"].get("latest", {})}
        """
    ).strip()
    response = _assistant_response(prompt, payload["settings"].get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not draft metadata right now."}


@app.post("/api/creator-actions/metadata/publish")
def publish_metadata(request: MetadataPublishRequest) -> dict[str, Any]:
    if not request.reviewed:
        return {"success": False, "message": "Review confirmation is required before publishing."}
    success, message = update_owned_video_metadata(
        load_vault_settings(),
        request.video_id,
        request.title,
        request.description,
        request.tags,
    )
    if success:
        _log_action("metadata_update", {"video_id": request.video_id, "title": request.title, "tag_count": len(request.tags)})
        save_cached_owned_video_metadata(
            request.video_id,
            {
                "video_id": request.video_id,
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "category_id": "10",
                "thumbnail_url": "",
                "privacy_status": "",
            },
            "Metadata cache updated after local publish action.",
        )
    return {"success": success, "message": message}


@app.post("/api/creator-actions/comments/list")
def list_comments(request: CommentListRequest) -> dict[str, Any]:
    rows, message = cached_comment_threads(load_vault_settings(), video_id=request.video_id, max_results=20)
    return _json_safe({"rows": rows, "message": message})


@app.post("/api/creator-actions/comments/draft")
def draft_comment(request: CommentDraftRequest) -> dict[str, str]:
    settings = load_vault_settings()
    prompt = textwrap.dedent(
        f"""
        Draft one warm, natural YouTube reply from Ralskies.
        Keep it specific, non-spammy, and under 300 characters.
        Do not overpromise. Do not use repeated promotional language.

        Comment author: {request.author}
        Comment: {request.text}
        """
    ).strip()
    response = _assistant_response(prompt, settings.get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not draft a reply right now."}


@app.post("/api/creator-actions/comments/publish")
def publish_comment(request: CommentPublishRequest) -> dict[str, Any]:
    if not request.reviewed:
        return {"success": False, "message": "Review confirmation is required before posting."}
    success, message = reply_to_comment(load_vault_settings(), request.comment_id, request.reply_text)
    if success:
        _log_action("comment_reply", {"comment_id": request.comment_id})
    return {"success": success, "message": message}
