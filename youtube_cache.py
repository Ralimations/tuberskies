from __future__ import annotations

import hashlib
import json
from datetime import date
from io import StringIO
from typing import Any

import pandas as pd

from storage import load_api_cache, save_api_cache
from youtube_client import (
    get_live_channel_profile,
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


def _cached_message(message: str, cache_date: str) -> str:
    if not message:
        return f"Loaded from local daily cache for {cache_date}."
    return f"{message} Loaded from local daily cache for {cache_date}."


def _stale_message(message: str, cache_date: str, error_message: str) -> str:
    detail = error_message or "Live refresh failed."
    return f"{message} Using last saved cache from {cache_date}. Refresh note: {detail}"


def cached_channel_profile(settings: dict[str, str], force_refresh: bool = False) -> tuple[dict[str, Any] | None, str]:
    cache_key = "youtube:channel_profile"
    today = _today_key()

    if not force_refresh:
        cached = load_api_cache(cache_key, today)
        profile = _payload_to_dict(cached.get("payload") if cached else None)
        if profile is not None:
            return profile, _cached_message(cached.get("message", ""), today)

    profile, message = get_live_channel_profile(settings)
    if profile is not None:
        save_api_cache(cache_key, today, _dict_to_payload(profile), message)
        return profile, f"{message} Saved to today's local cache."

    stale = load_api_cache(cache_key)
    stale_profile = _payload_to_dict(stale.get("payload") if stale else None)
    if stale_profile is not None:
        return stale_profile, _stale_message(stale.get("message", ""), stale["cache_date"], message)

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

    frame, message = load_live_analytics(settings, days=days)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    stale = load_api_cache(cache_key)
    stale_frame = _payload_to_dataframe(stale.get("payload") if stale else None)
    if stale_frame is not None:
        stale_frame["date"] = pd.to_datetime(stale_frame["date"], errors="coerce")
        return stale_frame, _stale_message(stale.get("message", ""), stale["cache_date"], message)

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

    frame, message = load_video_performance(settings, days=days, max_results=max_results)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    stale = load_api_cache(cache_key)
    stale_frame = _payload_to_dataframe(stale.get("payload") if stale else None)
    if stale_frame is not None:
        stale_frame["published_at"] = pd.to_datetime(stale_frame["published_at"], errors="coerce")
        return stale_frame, _stale_message(stale.get("message", ""), stale["cache_date"], message)

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

    frame, message = search_music_trends(settings, cleaned_queries, max_results_per_query=max_results_per_query)
    if frame is not None:
        save_api_cache(cache_key, today, _dataframe_to_payload(frame), message)
        return frame, f"{message} Saved to today's local cache."

    stale = load_api_cache(cache_key)
    stale_frame = _payload_to_dataframe(stale.get("payload") if stale else None)
    if stale_frame is not None:
        stale_frame["published_at"] = pd.to_datetime(stale_frame["published_at"], errors="coerce")
        return stale_frame, _stale_message(stale.get("message", ""), stale["cache_date"], message)

    return None, message
