from __future__ import annotations

import textwrap
import base64
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import ollama
import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
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
    get_trend_rows,
)
from aria_app.features.command_center_parts.keyword_tools import build_keyword_opportunity_df, build_title_scorecard
from aria_app.features.command_center_parts.upload_metrics import build_upload_takeaways
from aria_app.pattern_memory import refresh_pattern_memory
from mock_data import generate_analytics_data
from shorts_architect import SHORTS_OUTPUT_DIR, SHORTS_WORKDIR, analyze_video_pipeline, preview_shorts_frames, render_ai_shorts, sample_video_frames, save_uploaded_bytes
from storage import (
    PRIORITIES,
    STAGES,
    delete_shorts_project,
    list_api_cache_rows,
    list_shorts_projects,
    load_calendar,
    load_shorts_project,
    load_vault_settings,
    save_calendar,
    save_shorts_project,
    save_vault_settings,
    database_status,
)
from youtube_cache import (
    cached_channel_profile,
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
    {"label": "A.R.I.A. Memory", "path": "/pattern-memory", "icon": "memory", "group": "More tools"},
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


class VaultSettingsRequest(BaseModel):
    default_description: str = ""
    youtube_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    ollama_model: str = "gemma"
    ollama_vision_model: str = ""


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
    reason: str = ""
    current_title: str = ""


class UploadTipsRequest(BaseModel):
    upload: dict[str, Any]
    upload_kind: str = "Full Length"


class MetadataLoadRequest(BaseModel):
    video_id: str


class MetadataPublishRequest(BaseModel):
    video_id: str
    title: str
    description: str
    tags: list[str]
    reviewed: bool = False


class ShortsPlanClip(BaseModel):
    segment_id: int | None = None
    start: float = 0.0
    end: float = 35.0
    title: str = ""
    hook: str = ""
    caption_lines: list[str] = []
    reason: str = ""
    score: float = 0.0


class ShortsRenderRequest(BaseModel):
    main_video_path: str
    broll_video_path: str = ""
    shorts: list[ShortsPlanClip]
    layout_mode: str = "Solo Mode"
    text_color: str = "#ffd166"
    add_outline: bool = True


class ShortsPreviewRequest(BaseModel):
    main_video_path: str
    shorts: list[ShortsPlanClip]


class ShortsProjectSaveRequest(BaseModel):
    id: str = ""
    title: str = "Untitled Shorts Project"
    payload: dict[str, Any]


ACTION_LOG_PATH = Path(__file__).resolve().parents[1] / "data" / "creator_action_log.jsonl"
FREE_VISION_MODELS = [
    {"name": "moondream", "label": "moondream - lightweight free vision model"},
    {"name": "minicpm-v", "label": "minicpm-v - stronger free vision model"},
    {"name": "llava:7b", "label": "llava:7b - classic free vision model"},
]
VISION_MODEL_PREFIXES = ("moondream", "minicpm-v", "llava", "llama3.2-vision", "granite3.2-vision", "mistral-small3.1")


def _log_action(action: str, payload: dict[str, object]) -> None:
    ACTION_LOG_PATH.parent.mkdir(exist_ok=True)
    row = {"created_at": datetime.now().isoformat(timespec="seconds"), "action": action, "payload": payload}
    with ACTION_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _model_name(model: Any) -> str:
    if isinstance(model, dict):
        return str(model.get("model") or model.get("name") or "").strip()
    return str(getattr(model, "model", "") or getattr(model, "name", "") or "").strip()


def _list_ollama_models() -> list[str]:
    try:
        response = ollama.list()
    except Exception:
        return []
    models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
    return sorted({_model_name(model) for model in models if _model_name(model)})


def _is_known_free_vision_model(model_name: str) -> bool:
    clean_name = model_name.lower().split(":")[0]
    return any(clean_name == prefix or model_name.lower().startswith(f"{prefix}:") for prefix in VISION_MODEL_PREFIXES)


def _list_free_vision_models(installed_models: list[str]) -> list[str]:
    return [model for model in installed_models if _is_known_free_vision_model(model)]


def _resolve_shorts_path(raw_path: str, allow_empty: bool = False) -> Path | None:
    if not raw_path and allow_empty:
        return None
    path = Path(raw_path).expanduser().resolve()
    allowed_roots = [SHORTS_WORKDIR.resolve(), SHORTS_OUTPUT_DIR.resolve()]
    if not any(path == root or root in path.parents for root in allowed_roots):
        raise ValueError("Shorts render paths must come from the local Shorts workspace.")
    if not path.exists():
        raise ValueError(f"Shorts file was not found: {path}")
    return path


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = raw_text.strip()
    if not cleaned:
        return None
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    try:
        payload = json.loads(cleaned)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            payload = json.loads(cleaned[start : end + 1])
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None
    return None


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


def _metadata_action_rows(video_df: pd.DataFrame | None) -> list[dict[str, Any]]:
    if video_df is None or video_df.empty:
        return []

    frame = video_df.copy()
    for column in ["views", "retention", "engagement_score", "watch_time_hours"]:
        if column not in frame.columns:
            frame[column] = 0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)

    median_views = float(frame["views"].median()) if len(frame) > 1 else 1_000
    median_retention = float(frame["retention"].median()) if len(frame) > 1 else 45
    frame["priority_score"] = (
        frame["engagement_score"].rank(method="dense", ascending=True)
        + frame["views"].rank(method="dense", ascending=True)
        + frame["retention"].rank(method="dense", ascending=True)
    )
    frame["needs_metadata"] = (frame["views"] < median_views) | (frame["retention"] < median_retention)
    selected = frame[frame["needs_metadata"]].sort_values(["priority_score", "views"], ascending=True).head(8)
    if selected.empty:
        selected = frame.sort_values(["engagement_score", "views"], ascending=True).head(5)

    rows: list[dict[str, Any]] = []
    for _, row in selected.iterrows():
        reasons: list[str] = []
        if float(row.get("views", 0)) < median_views:
            reasons.append("lower views")
        if float(row.get("retention", 0)) < median_retention:
            reasons.append("weaker retention")
        if not reasons:
            reasons.append("lowest optimization score")
        suggestion = "Refresh title promise, description opening, and focused tags."
        if "weaker retention" in reasons and "lower views" in reasons:
            suggestion = "Reframe the title hook, tighten the first description line, and add searchable story tags."
        elif "weaker retention" in reasons:
            suggestion = "Check title promise against viewer retention and make the description set expectations faster."
        elif "lower views" in reasons:
            suggestion = "Improve discoverability with a clearer title angle and stronger keyword tags."
        rows.append(
            {
                "video_id": str(row.get("video_id", "")),
                "title": str(row.get("title", "Untitled Video")),
                "label": f"{str(row.get('title', 'Untitled Video'))[:90]} | {int(row.get('views', 0)):,} views",
                "views": int(row.get("views", 0)),
                "retention": round(float(row.get("retention", 0)), 1),
                "watch_time_hours": round(float(row.get("watch_time_hours", 0)), 1),
                "engagement_score": round(float(row.get("engagement_score", 0)), 1),
                "reason": ", ".join(reasons),
                "suggestion": suggestion,
            }
        )
    return rows


def _load_context() -> dict[str, Any]:
    settings = load_vault_settings()
    calendar_df = load_calendar()
    cache_freshness = _build_cache_freshness_rows()
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
        "cache_freshness": cache_freshness,
    }


def _preview_frame(frame: pd.DataFrame, columns: list[str], rows: int = 8) -> str:
    if frame is None or frame.empty:
        return "No rows available."
    available_columns = [column for column in columns if column in frame.columns]
    if not available_columns:
        return "No matching columns available."
    return frame[available_columns].head(rows).to_csv(index=False)


def _chat_freshness_context(cache_rows: list[dict[str, str]]) -> str:
    if not cache_rows:
        return "No YouTube cache freshness rows are available yet."

    important = {"Analytics", "Upload Performance", "Channel Profile"}
    lines: list[str] = []
    for row in cache_rows:
        if row.get("dataset") not in important:
            continue
        latest = row.get("latest_data_date") or "none"
        today = row.get("today_date") or "not checked"
        lines.append(
            f"- {row.get('dataset')}: {row.get('status')} | latest usable data {latest} | today {today}"
        )

    return "\n".join(lines) if lines else "No primary YouTube cache rows are available yet."


def _frame_visual_notes(frame_paths: list[Path], vision_model: str) -> str:
    if not frame_paths or not vision_model.strip():
        return "No visual model was provided, so this run uses audio, transcript, and timing signals only."
    try:
        images = [base64.b64encode(path.read_bytes()).decode("ascii") for path in frame_paths[:6]]
        response = ollama.chat(
            model=vision_model.strip(),
            messages=[
                {
                    "role": "user",
                    "content": (
                        "These are sampled frames from a music performance video. "
                        "Describe visual energy, framing, facial/performance intensity, and any moments that may work as Shorts."
                    ),
                    "images": images,
                }
            ],
        )
        content = str(response.get("message", {}).get("content", "")).strip()
        return content or "The visual model returned no visual notes."
    except Exception as error:
        return f"Visual pass skipped: {error}"


def _build_ai_shorts_prompt(
    segments: list[dict[str, float]],
    transcript_df: pd.DataFrame,
    source_name: str,
    layout_mode: str,
    objective: str,
    visual_notes: str,
) -> str:
    transcript_preview = _preview_frame(
        transcript_df,
        ["segment_id", "start_time", "end_time", "text"],
        rows=40,
    )
    return textwrap.dedent(
        f"""
        You are A.R.I.A. acting as an AI Shorts director for Ralskies.
        You are choosing Shorts from a full music performance using audio-energy windows, transcription, and optional visual notes.
        Do not ask the creator to manually choose cuts. Pick the cuts yourself.

        Source video: {source_name}
        Requested layout: {layout_mode}
        Objective: {objective}

        Detected high-energy windows:
        {json.dumps(segments, indent=2)}

        Transcript rows:
        {transcript_preview}

        Visual notes:
        {visual_notes}

        Return only valid JSON with this shape:
        {{
          "video_title": "overall source video title idea",
          "shorts": [
            {{
              "segment_id": 1,
              "start": 0.0,
              "end": 35.0,
              "title": "YouTube Shorts title",
              "hook": "first caption / on-screen hook",
              "caption_lines": ["short subtitle line", "another subtitle line"],
              "reason": "why this cut should retain viewers",
              "score": 88
            }}
          ],
          "posting_notes": ["note about title, pinned comment, or sequencing"]
        }}
        Keep captions natural for music. Prefer emotional, theatrical, high-retention hooks.
        """
    ).strip()


def _fallback_ai_shorts_plan(segments: list[dict[str, float]], transcript_df: pd.DataFrame, source_name: str, objective: str) -> dict[str, Any]:
    shorts: list[dict[str, Any]] = []
    for index, segment in enumerate(segments[:5], start=1):
        rows = transcript_df[transcript_df["segment_id"] == index] if "segment_id" in transcript_df.columns else pd.DataFrame()
        text = " ".join(rows["text"].fillna("").astype(str).head(2).tolist()).strip()
        shorts.append(
            {
                "segment_id": index,
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "title": f"{source_name[:70]} | {objective}",
                "hook": text[:90] or "Wait for this vocal moment",
                "caption_lines": [line for line in [text[:80], text[80:160]] if line],
                "reason": "Chosen from the highest-energy detected music windows.",
                "score": round(float(segment.get("score", 0)) * 100, 1),
            }
        )
    return {"video_title": source_name, "shorts": shorts, "posting_notes": ["AI fallback used because the local model did not return valid JSON."]}


def _normalize_ai_shorts_plan(plan: dict[str, Any] | None, segments: list[dict[str, float]], transcript_df: pd.DataFrame, source_name: str, objective: str) -> dict[str, Any]:
    if not isinstance(plan, dict):
        plan = _fallback_ai_shorts_plan(segments, transcript_df, source_name, objective)

    raw_shorts = plan.get("shorts")
    if not isinstance(raw_shorts, list) or not raw_shorts:
        plan = _fallback_ai_shorts_plan(segments, transcript_df, source_name, objective)
        raw_shorts = plan.get("shorts", [])

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw_shorts[:8], start=1):
        if not isinstance(item, dict):
            continue
        segment = segments[min(index - 1, len(segments) - 1)] if segments else {"start": 0.0, "end": 35.0}
        start = float(item.get("start", segment.get("start", 0.0)) or 0.0)
        end = float(item.get("end", segment.get("end", start + 35.0)) or start + 35.0)
        start = max(0.0, round(start, 2))
        end = round(max(start + 3.0, end), 2)
        raw_lines = item.get("caption_lines")
        caption_lines = [str(line).strip() for line in raw_lines if str(line).strip()] if isinstance(raw_lines, list) else []
        hook = str(item.get("hook") or "").strip()
        if not caption_lines and hook:
            caption_lines = [hook]
        normalized.append(
            {
                "segment_id": int(item.get("segment_id") or index),
                "start": start,
                "end": end,
                "title": str(item.get("title") or f"{source_name[:60]} Short {index}").strip(),
                "hook": hook or "Wait for this vocal moment",
                "caption_lines": caption_lines or ["Wait for this moment"],
                "reason": str(item.get("reason") or "Chosen from the strongest detected music moment.").strip(),
                "score": float(item.get("score") or 70),
            }
        )

    if not normalized:
        return _fallback_ai_shorts_plan(segments, transcript_df, source_name, objective)

    posting_notes = plan.get("posting_notes")
    return {
        "video_title": str(plan.get("video_title") or source_name).strip(),
        "shorts": normalized,
        "posting_notes": [str(note).strip() for note in posting_notes if str(note).strip()] if isinstance(posting_notes, list) else [],
    }


def _shorts_error_message(error: Exception, stage: str) -> str:
    text = str(error)
    lower = text.lower()
    if isinstance(error, ModuleNotFoundError):
        return f"{stage} could not start because a Python package is missing: {error.name}. Run pip install -r requirements.txt, then try again."
    if "ffmpeg" in lower or "ffprobe" in lower:
        return f"{stage} needs FFmpeg available on PATH. Install FFmpeg, restart the terminal, then rerun A.R.I.A. Studio."
    if "imagemagick" in lower or "textclip" in lower or "convert-im6" in lower:
        return f"{stage} reached caption rendering, but MoviePy could not create text clips. Install ImageMagick or switch MoviePy text support on this machine, then render again."
    if "no audio" in lower:
        return f"{stage} needs a full performance video with an audio track. Upload a video file that includes the music."
    if "model" in lower and ("whisper" in lower or "download" in lower):
        return f"{stage} could not load the selected Whisper model. Try the tiny or base model first, or use the future model-download setting once we add it."
    return f"{stage} failed: {text}"


def _chat_context(payload: dict[str, Any]) -> str:
    analytics_df = payload["analytics_df"]
    video_df = payload["video_df"]
    calendar_df = payload["calendar_df"]
    today_payload = payload["today_payload"]
    upload_takeaways = payload["upload_takeaways"]
    pattern_snapshot = payload["pattern_memory"].get("latest")
    freshness_context = textwrap.indent(_chat_freshness_context(payload.get("cache_freshness", [])), "        ")

    last_30 = analytics_df.tail(30) if analytics_df is not None else pd.DataFrame()
    views_30 = int(last_30["views"].fillna(0).sum()) if not last_30.empty and "views" in last_30 else 0
    watch_hours_30 = float(last_30["watch_time_hours"].fillna(0).sum()) if not last_30.empty and "watch_time_hours" in last_30 else 0
    uploads_count = int(len(video_df)) if video_df is not None else 0
    analytics_count = int(len(analytics_df)) if analytics_df is not None else 0
    calendar_count = int(len(calendar_df)) if calendar_df is not None else 0
    best = upload_takeaways.get("best")
    weak = upload_takeaways.get("weak")
    shorts_projects = list_shorts_projects()
    latest_shorts_project = shorts_projects[0] if shorts_projects else None
    shorts_context = (
        f"{len(shorts_projects)} saved Shorts project(s). Latest: {latest_shorts_project.get('title', 'Untitled')} updated {latest_shorts_project.get('updated_at', '')}."
        if latest_shorts_project
        else "No saved Shorts analysis projects yet. Shorts Architect can analyze uploaded performances, create AI cut plans, preview frames, and render MP4s after a video is uploaded."
    )

    return textwrap.dedent(
        f"""
        Current Ralskies analytics context:
        - Data source: {payload["source"]}
        Data freshness:
        {freshness_context}
        - Last 30 days views: {views_30:,}
        - Last 30 days watch time hours: {watch_hours_30:.1f}
        - Stored analytics rows available: {analytics_count}
        - Stored upload rows available: {uploads_count}
        - Stored repertoire rows available: {calendar_count}
        - Today focus: {today_payload.get("focus_title", "unknown")}
        - Today risk: {today_payload.get("risk_title", "unknown")} | {today_payload.get("risk_reason", "")}
        - Today opportunity: {today_payload.get("opportunity_title", "unknown")} | {today_payload.get("opportunity_reason", "")}
        - Best upload: {best.to_dict() if hasattr(best, "to_dict") else best}
        - Weakest upload: {weak.to_dict() if hasattr(weak, "to_dict") else weak}
        - Shorts Architect: {shorts_context}
        - Pattern memory snapshot: {pattern_snapshot or {}}

        Recent daily analytics:
        {_preview_frame(analytics_df.tail(14), ["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"], 14)}

        Top uploads:
        {_preview_frame(video_df, ["title", "views", "retention", "watch_time_hours", "subscribers_gained", "engagement_score"], 8)}

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
        The Analytics context below is your current stored database/cache context. Use it for any custom user wording, not only suggested prompt text.
        Do not say "I do not have specific data in the current context" when the relevant stored rows or summaries are shown below. Instead, answer from the available rows and name any limits.
        If the creator is only greeting you, testing the chat, thanking you, or making small talk, respond naturally in one short sentence and do not give analytics recommendations yet.
        Only give analytics recommendations when the creator asks for advice, analysis, decisions, risks, patterns, uploads, Shorts, metadata, or next actions.
        If the creator asks about Shorts and there are no saved Shorts projects yet, explain what Shorts Architect can do and suggest the next upload/analyze step instead of saying there is no Shorts data.

        Analytics context:
        {context}

        Recent chat:
        {recent_chat or "No prior chat in this session."}

        Creator question:
        {message}
        """
    ).strip()


def _direct_chat_response(message: str, payload: dict[str, Any]) -> str | None:
    lowered = message.lower()
    if "short" not in lowered:
        return None

    projects = list_shorts_projects()
    video_df = payload["video_df"]
    if projects:
        latest = projects[0]
        return (
            f"You have {len(projects)} saved Shorts Architect project(s). "
            f"The latest is {latest.get('title', 'Untitled')}. Open Shorts Architect to preview, edit, or render the saved AI cut plan."
        )

    if video_df is None or video_df.empty:
        return (
            "No saved Shorts projects or upload rows are available yet. "
            "Next step: upload a full video in Shorts Architect, let A.R.I.A. analyze the music and frames, then generate the cut plan."
        )

    candidates = video_df.copy()
    if "engagement_score" in candidates.columns:
        candidates["_rank"] = pd.to_numeric(candidates["engagement_score"], errors="coerce").fillna(0)
    elif "views" in candidates.columns:
        candidates["_rank"] = pd.to_numeric(candidates["views"], errors="coerce").fillna(0)
    else:
        candidates["_rank"] = 0
    top_rows = candidates.sort_values("_rank", ascending=False).head(3)
    lines = []
    for index, row in enumerate(top_rows.to_dict(orient="records"), start=1):
        title = str(row.get("title") or "Untitled upload")
        views = row.get("views", "unknown views")
        retention = row.get("retention", "unknown retention")
        lines.append(f"{index}. {title} | views: {views} | retention: {retention}")
    return (
        "No saved Shorts Architect projects yet, but the stored upload data gives us candidates to test first:\n"
        + "\n".join(lines)
        + "\nNext step: upload the strongest full performance in Shorts Architect and let A.R.I.A. pick cuts, titles, captions, and renderable clips."
    )


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
def health() -> dict[str, Any]:
    return {"status": "ok", "database": database_status()}


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
            "cache": payload["cache_freshness"],
        }
    )


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, str]:
    small_talk = _small_talk_response(request.message)
    if small_talk:
        return {"role": "assistant", "content": small_talk}
    payload = _load_context()
    direct_response = _direct_chat_response(request.message, payload)
    if direct_response:
        return {"role": "assistant", "content": direct_response}
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
    direct_response = _direct_chat_response(request.message, payload)
    if direct_response:
        return StreamingResponse(iter([direct_response]), media_type="text/plain")
    prompt = _build_chat_prompt(request.message, request.history, _chat_context(payload))
    model = payload["settings"].get("ollama_model", "gemma")
    return StreamingResponse(_stream_assistant_response(prompt, model), media_type="text/plain")


@app.post("/api/ideation/generate")
def generate_ideation(request: IdeationRequest) -> dict[str, str]:
    payload = _load_context()
    action = request.action
    if action == "fan_request_spin":
        prompt = build_coach_prompt(request.fan_request or request.topic, request.working_title, "fan_request_spin")
    else:
        prompt = build_coach_prompt(request.topic, request.working_title, action)
    response = _assistant_response(prompt, payload["settings"].get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not generate an ideation response."}


@app.post("/api/ideation/score")
def score_ideation(request: IdeationRequest) -> dict[str, Any]:
    try:
        calendar_df = load_calendar()
        keywords = build_keyword_opportunity_df(request.topic, request.working_title, calendar_df)
        scorecard = build_title_scorecard(request.working_title, request.topic)
    except Exception as error:
        keywords = pd.DataFrame(columns=["keyword", "demand", "competition", "channel_fit", "score"])
        scorecard = [("Packaging Score", "Unavailable"), ("Scoring Status", f"Keyword scoring failed: {error}")]
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
    trend_rows = get_trend_rows(analytics_df).copy()
    timing_df = build_publish_timing_table(analytics_df)
    audit_rows = build_channel_audit_rows(analytics_df, calendar_df, payload["settings"])

    for frame in (analytics_rows, trend_rows):
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
            "alerts": trend_rows,
            "publishTiming": timing_df,
            "auditRows": [{"label": label, "value": value} for label, value in audit_rows],
            "actionCards": _build_react_action_cards(payload),
            "messages": payload["messages"],
        }
    )


@app.post("/api/upload-lab/tips")
def draft_upload_lab_tips(request: UploadTipsRequest) -> dict[str, str]:
    settings = load_vault_settings()
    prompt = textwrap.dedent(
        f"""
        Give concise optimization tips for this Ralskies upload.
        Return:
        1. What to keep
        2. What to change in title/thumbnail promise/description
        3. One next upload lesson

        Upload type: {request.upload_kind}
        Upload metrics:
        {json.dumps(request.upload, indent=2, ensure_ascii=False)}
        """
    ).strip()
    response = _assistant_response(prompt, settings.get("ollama_model", "gemma"))
    return {"content": response or "A.R.I.A. could not draft upload tips right now."}


@app.get("/api/vault")
def vault() -> dict[str, Any]:
    settings = load_vault_settings()
    status = get_connection_status(settings)
    ollama_models = _list_ollama_models()
    return {
        "settings": settings,
        "ollama_models": ollama_models,
        "ollama_vision_models": _list_free_vision_models(ollama_models),
        "recommended_free_vision_models": FREE_VISION_MODELS,
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
            "OLLAMA_VISION_MODEL": request.ollama_vision_model,
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
    metadata_actions = _metadata_action_rows(video_df)
    return _json_safe(
        {
            "videos": _video_options(video_df),
            "metadataActions": metadata_actions,
            "message": video_message,
            "guardrails": [
                ("No autopilot", "A.R.I.A. drafts only; you approve each publish."),
                ("Lowest first", "Metadata actions prioritize weaker uploads before healthy ones."),
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
        1. Suggested title option if the current title should change
        2. A refined description opening
        3. A comma-separated tag list under 450 total characters
        4. Why this fix should help this low-performing upload
        5. One caution if the current title should not be changed

        Current video: {request.video_label}
        Why this was prioritized: {request.reason or "This upload was selected for metadata optimization."}
        Current title if known: {request.current_title or request.video_label}
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


@app.post("/api/shorts/ai-analyze")
def analyze_shorts_with_ai(
    main_video: UploadFile = File(...),
    broll_video: UploadFile | None = File(None),
    whisper_model: str = Form("small"),
    layout_mode: str = Form("Solo Mode"),
    objective: str = Form("Retention hook"),
    vision_model: str = Form(""),
) -> dict[str, Any]:
    warnings: list[str] = []
    empty_response = {
        "success": False,
        "message": "Shorts AI analysis did not complete.",
        "warnings": warnings,
        "main_video_path": "",
        "broll_video_path": "",
        "segments": [],
        "transcriptRows": [],
        "visualNotes": "",
        "aiPlan": {"shorts": [], "posting_notes": []},
        "rawModelResponse": "",
    }
    try:
        settings = load_vault_settings()
        active_vision_model = vision_model.strip() or settings.get("ollama_vision_model", "").strip()
        main_path = save_uploaded_bytes(main_video.filename or "main_video.mp4", main_video.file.read(), "main_video")
        broll_path = (
            save_uploaded_bytes(broll_video.filename or "broll_video.mp4", broll_video.file.read(), "broll_video")
            if broll_video is not None
            else None
        )
        segments, transcript_df = analyze_video_pipeline(main_path, whisper_model=whisper_model)
        if transcript_df.attrs.get("warning"):
            warnings.append(str(transcript_df.attrs["warning"]))
        try:
            frame_paths = sample_video_frames(main_path, frame_count=6)
        except Exception as error:
            frame_paths = []
            warnings.append(_shorts_error_message(error, "Visual frame sampling"))
        visual_notes = _frame_visual_notes(frame_paths, active_vision_model)
        if visual_notes.startswith("Visual pass skipped:"):
            warnings.append(visual_notes)
        prompt = _build_ai_shorts_prompt(
            segments=segments,
            transcript_df=transcript_df,
            source_name=main_video.filename or main_path.name,
            layout_mode=layout_mode,
            objective=objective,
            visual_notes=visual_notes,
        )
        model = settings.get("ollama_model", "gemma")
        raw_response = _assistant_response(prompt, model)
        parsed_plan = _extract_json_object(raw_response)
        if parsed_plan is None:
            warnings.append("The local text model did not return valid JSON, so A.R.I.A. used a fallback cut plan.")
        ai_plan = _normalize_ai_shorts_plan(parsed_plan, segments, transcript_df, main_video.filename or main_path.stem, objective)
        _log_action(
            "shorts_ai_analysis",
            {
                "main_video": str(main_path),
                "broll_video": str(broll_path) if broll_path else "",
                "segment_count": len(segments),
                "transcript_rows": len(transcript_df),
                "vision_model": active_vision_model,
                "warning_count": len(warnings),
            },
        )
        return _json_safe(
            {
                "success": True,
                "message": f"AI plan ready: {len(ai_plan.get('shorts', []))} cut(s) selected.",
                "warnings": warnings,
                "main_video_path": str(main_path),
                "broll_video_path": str(broll_path) if broll_path else "",
                "segments": segments,
                "transcriptRows": transcript_df,
                "visualNotes": visual_notes,
                "aiPlan": ai_plan,
                "rawModelResponse": raw_response,
            }
        )
    except Exception as error:
        empty_response["message"] = _shorts_error_message(error, "Shorts AI analysis")
        return _json_safe(empty_response)


@app.post("/api/shorts/render")
def render_shorts_from_ai_plan(request: ShortsRenderRequest) -> dict[str, Any]:
    try:
        main_path = _resolve_shorts_path(request.main_video_path)
        broll_path = _resolve_shorts_path(request.broll_video_path, allow_empty=True)
        if main_path is None:
            return {"success": False, "message": "A main video path is required.", "outputs": []}
        if request.layout_mode == "Duet Mode" and broll_path is None:
            return {"success": False, "message": "Duet Mode needs a B-Roll / Reference video. Switch to Solo Mode or upload B-Roll before rendering.", "outputs": []}
        if not request.shorts:
            return {"success": False, "message": "No cut plan was provided. Run AI Director or restore the AI plan before rendering.", "outputs": []}
        outputs = render_ai_shorts(
            main_video_path=main_path,
            broll_video_path=broll_path,
            shorts_plan=[clip.dict() for clip in request.shorts],
            layout_mode=request.layout_mode,
            text_color=request.text_color,
            add_outline=request.add_outline,
        )
        if not outputs:
            return {"success": False, "message": "No Shorts were rendered. Check that every cut has a valid start/end time inside the source video.", "outputs": []}
    except Exception as error:
        return {"success": False, "message": _shorts_error_message(error, "Shorts render"), "outputs": []}

    _log_action(
        "shorts_ai_render",
        {
            "main_video": str(main_path),
            "broll_video": str(broll_path) if broll_path else "",
            "output_count": len(outputs),
        },
    )
    return {
        "success": True,
        "message": f"Rendered {len(outputs)} Shorts export(s).",
        "outputs": [str(path) for path in outputs],
    }


@app.post("/api/shorts/preview-frames")
def preview_shorts_from_ai_plan(request: ShortsPreviewRequest) -> dict[str, Any]:
    try:
        main_path = _resolve_shorts_path(request.main_video_path)
        if main_path is None:
            return {"success": False, "message": "A main video path is required.", "frames": []}
        if not request.shorts:
            return {"success": False, "message": "No cut plan was provided. Run AI Director or restore the AI plan before previewing.", "frames": []}
        previews = preview_shorts_frames(main_path, [clip.dict() for clip in request.shorts])
        if not previews:
            return {"success": False, "message": "No preview frames were created. Check that every cut has a valid start/end time inside the source video.", "frames": []}
    except Exception as error:
        return {"success": False, "message": _shorts_error_message(error, "Shorts preview"), "frames": []}

    frames = []
    for preview in previews:
        frame_path = Path(str(preview["path"]))
        image_data = base64.b64encode(frame_path.read_bytes()).decode("ascii")
        frames.append(
            {
                "index": preview["index"],
                "start": preview["start"],
                "end": preview["end"],
                "timestamp": preview["timestamp"],
                "imageDataUrl": f"data:image/jpeg;base64,{image_data}",
            }
        )
    return {
        "success": True,
        "message": f"Built {len(frames)} cut preview frame(s).",
        "frames": frames,
    }


@app.get("/api/shorts/projects")
def list_saved_shorts_projects() -> dict[str, Any]:
    return {"projects": list_shorts_projects()}


@app.get("/api/shorts/projects/{project_id}")
def get_saved_shorts_project(project_id: str) -> dict[str, Any]:
    project = load_shorts_project(project_id)
    if project is None:
        return {"success": False, "message": "Shorts project was not found.", "project": None}
    return {"success": True, "message": "Shorts project loaded.", "project": project}


@app.post("/api/shorts/projects")
def save_saved_shorts_project(request: ShortsProjectSaveRequest) -> dict[str, Any]:
    project = save_shorts_project(
        {
            "id": request.id,
            "title": request.title,
            "payload": request.payload,
        }
    )
    return {"success": True, "message": "Shorts project saved.", "project": project, "projects": list_shorts_projects()}


@app.delete("/api/shorts/projects/{project_id}")
def remove_saved_shorts_project(project_id: str) -> dict[str, Any]:
    delete_shorts_project(project_id)
    return {"success": True, "message": "Shorts project deleted.", "projects": list_shorts_projects()}
