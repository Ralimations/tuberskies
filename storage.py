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
        "title": "Why My CTR Dropped Last Month",
        "stage": "Idea",
        "target_upload_date": "",
        "notes": "Break down thumbnails and titles from recent uploads.",
    },
    {
        "title": "3 Editing Tweaks That Improved Retention",
        "stage": "Scripting",
        "target_upload_date": "",
        "notes": "Use side-by-side examples from older videos.",
    },
]

STAGES = ["Idea", "Scripting", "Filming", "Editing", "Ready for Upload"]


def load_calendar() -> pd.DataFrame:
    if not CALENDAR_PATH.exists():
        save_calendar(pd.DataFrame(DEFAULT_CALENDAR_ROWS))

    with CALENDAR_PATH.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    frame = pd.DataFrame(rows)
    if frame.empty:
        frame = pd.DataFrame(DEFAULT_CALENDAR_ROWS)

    for column in ["title", "stage", "target_upload_date", "notes"]:
        if column not in frame.columns:
            frame[column] = ""

    return frame[["title", "stage", "target_upload_date", "notes"]]


def save_calendar(df: pd.DataFrame) -> None:
    sanitized = df.fillna("").to_dict(orient="records")
    with CALENDAR_PATH.open("w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2)


def load_vault_settings() -> dict[str, str]:
    values = dotenv_values(ENV_PATH)
    return {
        "default_description": str(values.get("DEFAULT_DESCRIPTION", "")),
        "youtube_api_key": str(values.get("YOUTUBE_API_KEY", "")),
        "youtube_client_id": str(values.get("YOUTUBE_CLIENT_ID", "")),
        "youtube_client_secret": str(values.get("YOUTUBE_CLIENT_SECRET", "")),
        "ollama_model": str(values.get("OLLAMA_MODEL", "gemma")),
    }


def save_vault_settings(settings: dict[str, Any]) -> None:
    for key, value in settings.items():
        set_key(str(ENV_PATH), key, str(value))
