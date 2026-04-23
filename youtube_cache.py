from __future__ import annotations

import hashlib
import json
from datetime import date
from io import StringIO
from typing import Any

import pandas as pd

from storage import load_api_cache, load_latest_api_cache, save_api_cache
from youtube_client import (
    get_owned_video_metadata,
    get_live_channel_profile,
    list_recent_comment_threads,
    load_live_analytics,
    load_video_performance,
    search_music_trends,
)


def _today_key() -> str:
    return date.today().isoformat()


def _dataframe_to_payload(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "kind": "dataframe",
        "value": frame.to_json(orient="split", date_format="iso"),
    }


def _payload_to_dataframe(payload: dict[str, Any] | None) -> pd.DataFrame | None:
    if not payload or payload.get("kind") != "dataframe":
        return None
    value = payload.get("value")
    if not isinstance(value, str):
        return None
    return pd.read_json(StringIO(value), orient="split")


def _dict_to_payload(value: dict[str, Any]) -> dict[str, Any]:
    return {"kind": "dict", "value": value}


def _payload_to_dict(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload or payload.get("kind") != "dict":
        return None
    value = payload.get("value")
    return value if isinstance(value, dict) else None


def _list_to_payload(value: list[dict[str, Any]]) -> dict[str, Any]:
    return {"kind": "list", "value": value}


def _payload_to_list(payload: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if not payload or payload.get("kind") != "list":
        return None
    value = payload.get("value")
    return value if isinstance(value, list) else None


def _refresh_error_payload(message: str) -> dict[str, Any]:
    return {"kind": "refresh_error", "value": {"message": message}}


def _is_refresh_error(payload: dict[str, Any] | None) -> bool:
    return bool(payload and payload.get("kind") == "refresh_error")


def _save_refresh_error(cache_key: str, cache_date: str, message: str) -> None:
    save_api_cache(cache_key, cache_date, _refresh_error_payload(message), message)


def _cached_message(message: str, cache_date: str) -> str:
    if not message:
        return f"Loaded from local daily cache for {cache_date}."
    return f"{message} Loaded from local daily cache for {cache_date}."


def _stale_message(message: str, cache_date: str, error_message: str) -> str:
    detail = error_message or "Live refresh failed."
    return f"{message} Using last saved cache from {cache_date}. Refresh note: {detail}"


def _load_stale_dataframe(cache_key: str, today: str, date_column: str) -> tuple[pd.DataFrame | None, str, str | None]:
    stale = load_latest_api_cache(cache_key, before_date=today, payload_kind="dataframe")
    stale_frame = _payload_to_dataframe(stale.get("payload") if stale else None)
    if stale_frame is not None:
        stale_frame[date_column] = pd.to_datetime(stale_frame[date_column], errors="coerce")
        return stale_frame, stale.get("message", ""), stale["cache_date"]
    return None, "", None


def _load_stale_dict(cache_key: str, today: str) -> tuple[dict[str, Any] | None, str, str | None]:
    stale = load_latest_api_cache(cache_key, before_date=today, payload_kind="dict")
    stale_value = _payload_to_dict(stale.get("payload") if stale else None)
    if stale_value is not None:
        return stale_value, stale.get("message", ""), stale["cache_date"]
    return None, "", None


def _load_stale_list(cache_key: str, today: str) -> tuple[list[dict[str, Any]] | None, str, str | None]:
    stale = load_latest_api_cache(cache_key, before_date=today, payload_kind="list")
    stale_value = _payload_to_list(stale.get("payload") if stale else None)
    if stale_value is not None:
        return stale_value, stale.get("message", ""), stale["cache_date"]
    return None, "", None


def cached_channel_profile(settings: dict[str, str], force_refresh: bool = False) -> tuple[dict[str, Any] | None, str]:
    cache_key = "youtube:channel_profile"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        profile = _payload_to_dict(cached.get("payload") if cached else None)
        if profile is not None:
            return profile, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_profile, stale_message, stale_date = _load_stale_dict(cache_key, today)
            if stale_profile is not None and stale_date:
                return stale_profile, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return None, cached.get("message", "Live refresh was already attempted today.")

    profile, message = get_live_channel_profile(settings)
    if profile is not None:
        save_api_cache(cache_key, today, _dict_to_payload(profile), message)
        return profile, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_profile, stale_message, stale_date = _load_stale_dict(cache_key, today)
    if stale_profile is not None and stale_date:
        return stale_profile, _stale_message(stale_message, stale_date, message)

    return None, message


def cached_live_analytics(settings: dict[str, str], days: int = 90, force_refresh: bool = False) -> tuple[pd.DataFrame | None, str]:
    cache_key = f"youtube:live_analytics:{days}"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        frame = _payload_to_dataframe(cached.get("payload") if cached else None)
        if frame is not None:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
            return frame, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "date")
            if stale_frame is not None and stale_date:
                return stale_frame, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return None, cached.get("message", "Live refresh was already attempted today.")

    frame, message = load_live_analytics(settings, days=days)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "date")
    if stale_frame is not None and stale_date:
        return stale_frame, _stale_message(stale_message, stale_date, message)

    return None, message


def cached_video_performance(
    settings: dict[str, str],
    days: int = 365,
    max_results: int = 100,
    force_refresh: bool = False,
) -> tuple[pd.DataFrame | None, str]:
    cache_key = f"youtube:video_performance:{days}:{max_results}"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        frame = _payload_to_dataframe(cached.get("payload") if cached else None)
        if frame is not None:
            frame["published_at"] = pd.to_datetime(frame["published_at"], errors="coerce")
            return frame, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "published_at")
            if stale_frame is not None and stale_date:
                return stale_frame, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return None, cached.get("message", "Live refresh was already attempted today.")

    frame, message = load_video_performance(settings, days=days, max_results=max_results)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "published_at")
    if stale_frame is not None and stale_date:
        return stale_frame, _stale_message(stale_message, stale_date, message)

    return None, message


def cached_music_trends(
    settings: dict[str, str],
    queries: list[str],
    max_results_per_query: int = 4,
    force_refresh: bool = False,
) -> tuple[pd.DataFrame | None, str]:
    cleaned_queries = [query.strip() for query in queries if query and query.strip()]
    query_hash = hashlib.sha256(json.dumps(cleaned_queries, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    cache_key = f"youtube:music_trends:{max_results_per_query}:{query_hash}"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        frame = _payload_to_dataframe(cached.get("payload") if cached else None)
        if frame is not None:
            frame["published_at"] = pd.to_datetime(frame["published_at"], errors="coerce")
            return frame, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "published_at")
            if stale_frame is not None and stale_date:
                return stale_frame, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return None, cached.get("message", "Live refresh was already attempted today.")

    frame, message = search_music_trends(settings, cleaned_queries, max_results_per_query=max_results_per_query)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_frame, stale_message, stale_date = _load_stale_dataframe(cache_key, today, "published_at")
    if stale_frame is not None and stale_date:
        return stale_frame, _stale_message(stale_message, stale_date, message)

    return None, message


def cached_owned_video_metadata(
    settings: dict[str, str],
    video_id: str,
    force_refresh: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    cleaned_video_id = video_id.strip()
    if not cleaned_video_id:
        return None, "Choose a video first."

    cache_key = f"youtube:video_metadata:{cleaned_video_id}"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        metadata = _payload_to_dict(cached.get("payload") if cached else None)
        if metadata is not None:
            return metadata, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_metadata, stale_message, stale_date = _load_stale_dict(cache_key, today)
            if stale_metadata is not None and stale_date:
                return stale_metadata, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return None, cached.get("message", "Live refresh was already attempted today.")

    metadata, message = get_owned_video_metadata(settings, cleaned_video_id)
    if metadata is not None:
        save_api_cache(cache_key, today, _dict_to_payload(metadata), message)
        return metadata, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_metadata, stale_message, stale_date = _load_stale_dict(cache_key, today)
    if stale_metadata is not None and stale_date:
        return stale_metadata, _stale_message(stale_message, stale_date, message)

    return None, message


def save_cached_owned_video_metadata(video_id: str, metadata: dict[str, Any], message: str = "Updated from local publish action.") -> None:
    cleaned_video_id = video_id.strip()
    if not cleaned_video_id:
        return
    save_api_cache(
        f"youtube:video_metadata:{cleaned_video_id}",
        _today_key(),
        _dict_to_payload(metadata),
        message,
    )


def cached_comment_threads(
    settings: dict[str, str],
    video_id: str = "",
    max_results: int = 20,
    force_refresh: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    cleaned_video_id = video_id.strip() or "channel"
    safe_max_results = min(max(max_results, 1), 50)
    cache_key = f"youtube:comment_threads:{cleaned_video_id}:{safe_max_results}"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        rows = _payload_to_list(cached.get("payload") if cached else None)
        if rows is not None:
            return rows, _cached_message(cached.get("message", ""), today)
        if cached and _is_refresh_error(cached.get("payload")):
            stale_rows, stale_message, stale_date = _load_stale_list(cache_key, today)
            if stale_rows is not None and stale_date:
                return stale_rows, _stale_message(stale_message, stale_date, cached.get("message", ""))
            return [], cached.get("message", "Live refresh was already attempted today.")

    rows, message = list_recent_comment_threads(settings, video_id=video_id, max_results=safe_max_results)
    if rows or message.startswith("Loaded recent"):
        save_api_cache(cache_key, today, _list_to_payload(rows), message)
        return rows, f"{message} Saved to today's local cache."

    _save_refresh_error(cache_key, today, message)
    stale_rows, stale_message, stale_date = _load_stale_list(cache_key, today)
    if stale_rows is not None and stale_date:
        return stale_rows, _stale_message(stale_message, stale_date, message)

    return [], message
