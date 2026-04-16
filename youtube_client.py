from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
TOKEN_PATH = DATA_DIR / "youtube_token.json"

YOUTUBE_ANALYTICS_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]


@dataclass(frozen=True)
class YouTubeConnectionStatus:
    connected: bool
    message: str


def _oauth_config(settings: dict[str, str]) -> dict[str, dict[str, Any]]:
    client_id = settings.get("youtube_client_id", "").strip()
    client_secret = settings.get("youtube_client_secret", "").strip()
    if not client_id or not client_secret:
        raise ValueError("Missing YouTube OAuth client credentials.")

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _load_stored_credentials() -> Credentials | None:
    if not TOKEN_PATH.exists():
        return None

    credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), YOUTUBE_ANALYTICS_SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")

    return credentials


def has_oauth_credentials(settings: dict[str, str]) -> bool:
    return bool(settings.get("youtube_client_id", "").strip() and settings.get("youtube_client_secret", "").strip())


def has_saved_token() -> bool:
    return TOKEN_PATH.exists()


def authorize_youtube_analytics(settings: dict[str, str]) -> str:
    flow = InstalledAppFlow.from_client_config(_oauth_config(settings), YOUTUBE_ANALYTICS_SCOPES)
    credentials = flow.run_local_server(
        host="localhost",
        port=0,
        authorization_prompt_message="A.R.I.A. is opening Google authorization in your browser...",
        success_message="A.R.I.A. authorization complete. You can close this window and return to the app.",
        open_browser=True,
    )
    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    return "YouTube Analytics authorization completed and the local token was saved."


def clear_youtube_token() -> None:
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


def get_connection_status(settings: dict[str, str]) -> YouTubeConnectionStatus:
    api_key = settings.get("youtube_api_key", "").strip()
    oauth_ready = has_oauth_credentials(settings)
    token_ready = has_saved_token()

    if not api_key and not oauth_ready:
        return YouTubeConnectionStatus(
            connected=False,
            message="Live YouTube data is not configured yet. Add your API key and OAuth client credentials in The Vault.",
        )

    if api_key and oauth_ready and token_ready:
        return YouTubeConnectionStatus(
            connected=True,
            message="API key, OAuth client credentials, and a saved YouTube token are all present. Live analytics should be available.",
        )

    if api_key and oauth_ready:
        return YouTubeConnectionStatus(
            connected=True,
            message="API key and OAuth client credentials are present. Finish the one-time Google authorization step to unlock live analytics.",
        )

    if api_key:
        return YouTubeConnectionStatus(
            connected=True,
            message="YouTube API key detected. Add OAuth client credentials to unlock live channel analytics.",
        )

    return YouTubeConnectionStatus(
        connected=False,
        message="OAuth client credentials are present, but the YouTube API key is still missing.",
    )


def build_youtube_data_client(settings: dict[str, str]) -> Any:
    api_key = settings.get("youtube_api_key", "").strip()
    if not api_key:
        raise ValueError("Missing YouTube API key.")

    return build("youtube", "v3", developerKey=api_key)


def _require_authorized_credentials(settings: dict[str, str]) -> tuple[Credentials | None, str | None]:
    status = get_connection_status(settings)
    if not status.connected:
        return None, status.message

    if not has_oauth_credentials(settings):
        return None, "OAuth client credentials are still missing, so live channel analytics cannot be requested yet."

    credentials = _load_stored_credentials()
    if credentials is None or not credentials.valid:
        return None, "OAuth is configured, but A.R.I.A. still needs the one-time Google authorization step."

    return credentials, None


def get_live_channel_profile(settings: dict[str, str]) -> tuple[dict[str, str] | None, str]:
    credentials, error_message = _require_authorized_credentials(settings)
    if credentials is None:
        return None, error_message or "Live YouTube authorization is not ready yet."

    try:
        youtube_client = build("youtube", "v3", credentials=credentials)
        channel_response = youtube_client.channels().list(part="snippet,statistics", mine=True).execute()
        channel_items = channel_response.get("items", [])
        if not channel_items:
            return None, "Google authorization succeeded, but no YouTube channel was returned for this account."

        channel = channel_items[0]
        snippet = channel.get("snippet", {})
        statistics = channel.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url", "")
        )
        return {
            "title": snippet.get("title", "YouTube Channel"),
            "handle": snippet.get("customUrl", ""),
            "thumbnail_url": thumbnail_url,
            "subscriber_count": statistics.get("subscriberCount", "0"),
            "video_count": statistics.get("videoCount", "0"),
        }, "Connected to the authorized YouTube channel."
    except HttpError as error:
        return None, f"YouTube Data API error while loading the channel profile: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while loading the YouTube channel profile: {error}"


def load_live_analytics(settings: dict[str, str], days: int = 90) -> tuple[pd.DataFrame | None, str]:
    credentials, error_message = _require_authorized_credentials(settings)
    if credentials is None:
        return None, error_message or "Live YouTube authorization is not ready yet."

    try:
        youtube_client = build("youtube", "v3", credentials=credentials)
        analytics_client = build("youtubeAnalytics", "v2", credentials=credentials)

        channel_response = youtube_client.channels().list(part="snippet", mine=True).execute()
        channel_items = channel_response.get("items", [])
        if not channel_items:
            return None, "Google authorization succeeded, but no YouTube channel was returned for this account."

        end_date = date.today()
        start_date = end_date - timedelta(days=max(days - 1, 1))

        analytics_response = analytics_client.reports().query(
            ids="channel==MINE",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics="views,estimatedMinutesWatched,subscribersGained,averageViewPercentage",
            dimensions="day",
            sort="day",
        ).execute()

        headers = [header["name"] for header in analytics_response.get("columnHeaders", [])]
        rows = analytics_response.get("rows", [])
        if not headers or not rows:
            return None, "The YouTube Analytics API returned no rows for this channel and date range."

        frame = pd.DataFrame(rows, columns=headers)
        frame["day"] = pd.to_datetime(frame["day"], errors="coerce")
        numeric_columns = [
            "views",
            "estimatedMinutesWatched",
            "subscribersGained",
            "averageViewPercentage",
        ]
        for column in numeric_columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        frame = frame.rename(
            columns={
                "day": "date",
                "averageViewPercentage": "retention",
                "estimatedMinutesWatched": "estimated_minutes_watched",
                "subscribersGained": "subscribers_gained",
            }
        )
        frame["ctr"] = pd.NA
        frame["watch_time_hours"] = frame["estimated_minutes_watched"].fillna(0) / 60
        frame = frame[["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"]]

        full_range = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq="D")})
        frame = full_range.merge(frame, on="date", how="left").sort_values("date")
        frame["views"] = frame["views"].fillna(0)
        frame["retention"] = frame["retention"].ffill().fillna(0)
        frame["watch_time_hours"] = frame["watch_time_hours"].fillna(0)
        frame["subscribers_gained"] = frame["subscribers_gained"].fillna(0)

        channel_title = channel_items[0].get("snippet", {}).get("title", "your YouTube channel")
        return frame, f"Live analytics loaded for {channel_title}."
    except HttpError as error:
        return None, f"YouTube Analytics API error: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while loading live analytics: {error}"
