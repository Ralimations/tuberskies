from __future__ import annotations

import textwrap
import json
from datetime import datetime
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
    build_creator_hero_stats,
    build_today_desk_payload,
)
from aria_app.features.command_center_parts.keyword_tools import build_keyword_opportunity_df, build_title_scorecard
from aria_app.features.command_center_parts.upload_metrics import build_upload_takeaways
from aria_app.pattern_memory import refresh_pattern_memory
from mock_data import generate_analytics_data
from storage import PRIORITIES, STAGES, load_calendar, load_vault_settings, save_calendar, save_vault_settings
from youtube_cache import cached_channel_profile, cached_live_analytics, cached_video_performance
from youtube_client import (
    get_owned_video_metadata,
    has_saved_token,
    list_recent_comment_threads,
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


@app.get("/api/vault")
def vault() -> dict[str, Any]:
    settings = load_vault_settings()
    return {
        "settings": settings,
        "connection": {
            "api_key": bool(settings.get("youtube_api_key", "").strip()),
            "oauth_client": bool(settings.get("youtube_client_id", "").strip() and settings.get("youtube_client_secret", "").strip()),
            "token": has_saved_token(),
        },
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
    metadata, message = get_owned_video_metadata(load_vault_settings(), request.video_id)
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
    return {"success": success, "message": message}


@app.post("/api/creator-actions/comments/list")
def list_comments(request: CommentListRequest) -> dict[str, Any]:
    rows, message = list_recent_comment_threads(load_vault_settings(), video_id=request.video_id, max_results=20)
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
