from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
TOKEN_PATH = DATA_DIR / "youtube_token.json"

YOUTUBE_ANALYTICS_SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
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


def _has_required_scopes(credentials: Credentials) -> bool:
    try:
        return credentials.has_scopes(YOUTUBE_ANALYTICS_SCOPES)
    except Exception:
        return False


def has_oauth_credentials(settings: dict[str, str]) -> bool:
    return bool(settings.get("youtube_client_id", "").strip() and settings.get("youtube_client_secret", "").strip())


def has_saved_token() -> bool:
    return TOKEN_PATH.exists()


def saved_token_has_required_scopes() -> bool:
    try:
        credentials = _load_stored_credentials()
    except Exception:
        return False
    return bool(credentials and _has_required_scopes(credentials))


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

    if api_key and oauth_ready and token_ready and not saved_token_has_required_scopes():
        return YouTubeConnectionStatus(
            connected=True,
            message="A saved YouTube token exists, but it is missing creator-management permission. Clear the local token and authorize again to publish metadata or replies.",
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

    try:
        credentials = _load_stored_credentials()
    except Exception as error:
        return None, f"The saved YouTube token could not be refreshed. Live YouTube data is unavailable until OAuth is working again: {error}"
    if credentials is None or not credentials.valid:
        return None, "OAuth is configured, but A.R.I.A. still needs the one-time Google authorization step."
    if not _has_required_scopes(credentials):
        return None, "The saved YouTube token is missing creator-management permission. Clear the local token in The Vault, then authorize YouTube again."

    return credentials, None


def _authorized_youtube_client(settings: dict[str, str]) -> tuple[Any | None, str | None]:
    credentials, error_message = _require_authorized_credentials(settings)
    if credentials is None:
        return None, error_message or "Live YouTube authorization is not ready yet."
    return build("youtube", "v3", credentials=credentials), None
