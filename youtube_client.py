from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from googleapiclient.discovery import build


@dataclass(frozen=True)
class YouTubeConnectionStatus:
    connected: bool
    message: str


def get_connection_status(settings: dict[str, str]) -> YouTubeConnectionStatus:
    api_key = settings.get("youtube_api_key", "").strip()
    if not api_key:
        return YouTubeConnectionStatus(
            connected=False,
            message="Live YouTube data is not configured yet. Add a YouTube API key in The Vault when you're ready.",
        )

    return YouTubeConnectionStatus(
        connected=True,
        message="API key found. Live YouTube wiring can be enabled from the dashboard.",
    )


def build_youtube_data_client(settings: dict[str, str]) -> Any:
    api_key = settings.get("youtube_api_key", "").strip()
    if not api_key:
        raise ValueError("Missing YouTube API key.")

    return build("youtube", "v3", developerKey=api_key)


def load_live_analytics_placeholder(settings: dict[str, str]) -> tuple[pd.DataFrame | None, str]:
    """
    Placeholder for future YouTube Analytics API support.

    Returns an empty result until OAuth credentials and channel selection are wired in.
    """
    status = get_connection_status(settings)
    if not status.connected:
        return None, status.message

    return None, (
        "API key detected, but live channel analytics are still intentionally empty until OAuth and "
        "YouTube Analytics API setup are added."
    )
