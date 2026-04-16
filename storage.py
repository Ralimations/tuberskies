from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import dotenv_values, set_key


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CALENDAR_PATH = DATA_DIR / "content_calendar.json"
ENV_PATH = BASE_DIR / ".env"

DEFAULT_CALENDAR_ROWS = [
    {
        "title": "Male Version of Pretty Little Baby",
        "stage": "Song Idea",
        "priority": "High",
        "content_pillar": "Reimagined Cover",
        "target_upload_date": None,
        "notes": "Lean theatrical and intimate, with a late-night starlight mood.",
    },
    {
        "title": "Into the Stars Live Session",
        "stage": "BandLab Recording",
        "priority": "Medium",
        "content_pillar": "Original Song",
        "target_upload_date": None,
        "notes": "Capture a dreamy celestial performance for the Fanskies.",
    },
]

STAGES = ["Song Idea", "Instrumental Prep", "BandLab Recording", "Video Editing", "Upload"]
PRIORITIES = ["Low", "Medium", "High"]
LEGACY_STAGE_MAP = {
    "Idea": "Song Idea",
    "Scripting": "Instrumental Prep",
    "Filming": "BandLab Recording",
    "Editing": "Video Editing",
    "Ready for Upload": "Upload",
}


def load_calendar() -> pd.DataFrame:
    if not CALENDAR_PATH.exists():
        save_calendar(pd.DataFrame(DEFAULT_CALENDAR_ROWS))

    with CALENDAR_PATH.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(DEFAULT_CALENDAR_ROWS)

    for column in ["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"]:
        if column not in frame.columns:
            frame[column] = None if column == "target_upload_date" else ""

    frame["title"] = frame["title"].fillna("").astype(str)
    frame["stage"] = (
        frame["stage"]
        .fillna(STAGES[0])
        .replace("", STAGES[0])
        .replace(LEGACY_STAGE_MAP)
        .astype(str)
    )
    frame["priority"] = frame["priority"].fillna("Medium").replace("", "Medium").astype(str)
    frame["content_pillar"] = frame["content_pillar"].fillna("").astype(str)
    frame["notes"] = frame["notes"].fillna("").astype(str)
    frame["target_upload_date"] = pd.to_datetime(frame["target_upload_date"], errors="coerce")

    return frame[["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"]]


def save_calendar(df: pd.DataFrame) -> None:
    sanitized_df = df.copy()
    sanitized_df["title"] = sanitized_df["title"].fillna("").astype(str)
    sanitized_df["stage"] = (
        sanitized_df["stage"]
        .fillna(STAGES[0])
        .replace("", STAGES[0])
        .replace(LEGACY_STAGE_MAP)
        .astype(str)
    )
    sanitized_df["priority"] = sanitized_df["priority"].fillna("Medium").replace("", "Medium").astype(str)
    sanitized_df["content_pillar"] = sanitized_df["content_pillar"].fillna("").astype(str)
    sanitized_df["notes"] = sanitized_df["notes"].fillna("").astype(str)
    sanitized_df["target_upload_date"] = pd.to_datetime(
        sanitized_df["target_upload_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    sanitized_df["target_upload_date"] = sanitized_df["target_upload_date"].fillna("")

    sanitized = sanitized_df.to_dict(orient="records")
    with CALENDAR_PATH.open("w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2)


def load_vault_settings() -> dict[str, str]:
    values = dotenv_values(ENV_PATH)
    return {
        "default_description": str(
            values.get(
                "DEFAULT_DESCRIPTION",
                "Best of Ralskies Playlist: https://www.youtube.com/\n"
                "Spotify: https://open.spotify.com/\n"
                "Apple Music: https://music.apple.com/\n"
                "Join the Fanskies on Discord: https://discord.gg/\n\n"
                "Gear used:\n"
                "- Sennheiser XS-1\n"
                "- M-Track DUO\n"
                "- BandLab\n",
            )
        ),
        "youtube_api_key": str(values.get("YOUTUBE_API_KEY", "")),
        "youtube_client_id": str(values.get("YOUTUBE_CLIENT_ID", "")),
        "youtube_client_secret": str(values.get("YOUTUBE_CLIENT_SECRET", "")),
        "ollama_model": str(values.get("OLLAMA_MODEL", "gemma")),
    }


def save_vault_settings(settings: dict[str, Any]) -> None:
    for key, value in settings.items():
        set_key(str(ENV_PATH), key, str(value))
