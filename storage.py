from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

import pandas as pd
from dotenv import dotenv_values, set_key

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional until PostgreSQL is configured
    psycopg = None
    dict_row = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CALENDAR_PATH = DATA_DIR / "content_calendar.json"
PATTERN_MEMORY_PATH = DATA_DIR / "pattern_memory.json"
DATABASE_PATH = DATA_DIR / "studio.db"
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


def _database_url() -> str:
    values = dotenv_values(ENV_PATH)
    return str(os.environ.get("DATABASE_URL") or values.get("DATABASE_URL") or "").strip()


def using_postgres() -> bool:
    return bool(_database_url())


def database_status() -> dict[str, Any]:
    database_url = _database_url()
    if not database_url:
        return {
            "backend": "sqlite",
            "label": "SQLite",
            "database": str(DATABASE_PATH),
            "host": "",
            "port": "",
        }

    parsed = urlparse(database_url)
    return {
        "backend": "postgres",
        "label": "PostgreSQL",
        "database": parsed.path.lstrip("/"),
        "host": parsed.hostname or "",
        "port": parsed.port or "",
    }


def _q(sql: str) -> str:
    return sql.replace("?", "%s") if using_postgres() else sql


@contextmanager
def _connect_database() -> Iterator[Any]:
    database_url = _database_url()
    if database_url:
        if psycopg is None:
            raise RuntimeError("DATABASE_URL is set, but psycopg is not installed. Run pip install -r requirements.txt.")
        connection = psycopg.connect(database_url, row_factory=dict_row)
        try:
            yield connection
        finally:
            connection.close()
        return

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def _execute(connection: Any, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> Any:
    return connection.execute(_q(sql), params)


def _executemany(connection: Any, sql: str, params: list[tuple[Any, ...]]) -> Any:
    if using_postgres():
        for param in params:
            connection.execute(_q(sql), param)
        return None
    return connection.executemany(_q(sql), params)


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    return row[index]


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def _upsert_app_kv_sql() -> str:
    return """
        INSERT INTO app_kv (key, value_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value_json = excluded.value_json,
            updated_at = CURRENT_TIMESTAMP
    """


def _upsert_pattern_memory_sql() -> str:
    return """
        INSERT INTO pattern_memory_snapshots (
            fingerprint, generated_at, snapshot_json
        )
        VALUES (?, ?, ?)
        ON CONFLICT(fingerprint) DO UPDATE SET
            generated_at = excluded.generated_at,
            snapshot_json = excluded.snapshot_json
    """


def _upsert_api_cache_sql() -> str:
    return """
        INSERT INTO api_cache (
            cache_key, cache_date, payload_json, message, updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(cache_key, cache_date) DO UPDATE SET
            payload_json = excluded.payload_json,
            message = excluded.message,
            updated_at = CURRENT_TIMESTAMP
    """


def initialize_database() -> None:
    with _connect_database() as connection:
        if using_postgres():
            _execute(
                connection,
                """
                CREATE TABLE IF NOT EXISTS content_calendar (
                    id SERIAL PRIMARY KEY,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    title TEXT NOT NULL DEFAULT '',
                    stage TEXT NOT NULL DEFAULT 'Song Idea',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    content_pillar TEXT NOT NULL DEFAULT '',
                    target_upload_date TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            _execute(
                connection,
                """
                CREATE TABLE IF NOT EXISTS pattern_memory_snapshots (
                    id SERIAL PRIMARY KEY,
                    fingerprint TEXT NOT NULL UNIQUE,
                    generated_at TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
        else:
            _execute(
                connection,
                """
                CREATE TABLE IF NOT EXISTS content_calendar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    title TEXT NOT NULL DEFAULT '',
                    stage TEXT NOT NULL DEFAULT 'Song Idea',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    content_pillar TEXT NOT NULL DEFAULT '',
                    target_upload_date TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            _execute(
                connection,
                """
                CREATE TABLE IF NOT EXISTS pattern_memory_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT NOT NULL UNIQUE,
                    generated_at TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS app_kv (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT NOT NULL,
                cache_date TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (cache_key, cache_date)
            )
            """,
        )
        _execute(
            connection,
            """
            CREATE TABLE IF NOT EXISTS shorts_projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        connection.commit()

    if not using_postgres():
        _migrate_api_cache_schema_if_needed()
    _migrate_json_calendar_if_needed()
    _migrate_json_pattern_memory_if_needed()


def _migrate_api_cache_schema_if_needed() -> None:
    with _connect_database() as connection:
        columns = connection.execute("PRAGMA table_info(api_cache)").fetchall()
        primary_key_columns = [row["name"] for row in sorted(columns, key=lambda item: item["pk"]) if row["pk"]]
        if primary_key_columns == ["cache_key", "cache_date"]:
            return

        connection.execute("ALTER TABLE api_cache RENAME TO api_cache_legacy")
        connection.execute(
            """
            CREATE TABLE api_cache (
                cache_key TEXT NOT NULL,
                cache_date TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (cache_key, cache_date)
            )
            """
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO api_cache (
                cache_key, cache_date, payload_json, message, created_at, updated_at
            )
            SELECT cache_key, cache_date, payload_json, message, created_at, updated_at
            FROM api_cache_legacy
            """
        )
        connection.execute("DROP TABLE api_cache_legacy")
        connection.commit()


def _normalize_calendar_frame(frame: pd.DataFrame) -> pd.DataFrame:
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


def _serialize_calendar_frame(df: pd.DataFrame) -> pd.DataFrame:
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
    return sanitized_df[["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"]]


def _load_calendar_rows_from_json() -> list[dict[str, Any]]:
    if not CALENDAR_PATH.exists():
        return DEFAULT_CALENDAR_ROWS
    with CALENDAR_PATH.open("r", encoding="utf-8") as file:
        rows = json.load(file)
    return rows if isinstance(rows, list) else DEFAULT_CALENDAR_ROWS


def _migrate_json_calendar_if_needed() -> None:
    with _connect_database() as connection:
        migrated = _execute(
            connection,
            "SELECT value_json FROM app_kv WHERE key = ?",
            ("calendar_json_migrated",),
        ).fetchone()
        if migrated:
            return

        count = _row_value(_execute(connection, "SELECT COUNT(*) AS count FROM content_calendar").fetchone(), "count", 0)
        if count:
            _execute(connection, _upsert_app_kv_sql(), ("calendar_json_migrated", "true"))
            connection.commit()
            return

        frame = _serialize_calendar_frame(_normalize_calendar_frame(pd.DataFrame(_load_calendar_rows_from_json())))
        rows = frame.to_dict(orient="records")
        _executemany(
            connection,
            """
            INSERT INTO content_calendar (
                sort_order, title, stage, priority, content_pillar, target_upload_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    row["title"],
                    row["stage"],
                    row["priority"],
                    row["content_pillar"],
                    row["target_upload_date"],
                    row["notes"],
                )
                for index, row in enumerate(rows)
            ],
        )
        _execute(connection, _upsert_app_kv_sql(), ("calendar_json_migrated", "true"))
        connection.commit()


def load_calendar() -> pd.DataFrame:
    initialize_database()
    with _connect_database() as connection:
        rows = _execute(
            connection,
            """
            SELECT title, stage, priority, content_pillar, target_upload_date, notes
            FROM content_calendar
            ORDER BY sort_order, id
            """
        ).fetchall()

    frame = pd.DataFrame([dict(row) for row in rows])
    return _normalize_calendar_frame(frame)


def save_calendar(df: pd.DataFrame) -> None:
    initialize_database()
    sanitized_df = _serialize_calendar_frame(df)
    rows = sanitized_df.to_dict(orient="records")
    with _connect_database() as connection:
        _execute(connection, "DELETE FROM content_calendar")
        _executemany(
            connection,
            """
            INSERT INTO content_calendar (
                sort_order, title, stage, priority, content_pillar, target_upload_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    index,
                    row["title"],
                    row["stage"],
                    row["priority"],
                    row["content_pillar"],
                    row["target_upload_date"],
                    row["notes"],
                )
                for index, row in enumerate(rows)
            ],
        )
        connection.commit()


def load_pattern_memory() -> dict[str, Any]:
    initialize_database()
    with _connect_database() as connection:
        rows = _execute(
            connection,
            """
            SELECT snapshot_json
            FROM pattern_memory_snapshots
            ORDER BY id DESC
            LIMIT 25
            """
        ).fetchall()

    snapshots: list[dict[str, Any]] = []
    for row in reversed(rows):
        try:
            snapshot = json.loads(row["snapshot_json"])
        except json.JSONDecodeError:
            continue
        if isinstance(snapshot, dict):
            snapshots.append(snapshot)

    if not snapshots:
        return {"history": [], "latest": None}

    return {"history": snapshots, "latest": snapshots[-1]}


def save_pattern_memory(memory: dict[str, Any]) -> None:
    initialize_database()
    history = memory.get("history", [])
    latest = memory.get("latest")
    snapshots = [item for item in history[-25:] if isinstance(item, dict)]
    if isinstance(latest, dict) and latest not in snapshots:
        snapshots.append(latest)

    with _connect_database() as connection:
        for snapshot in snapshots[-25:]:
            fingerprint = str(snapshot.get("fingerprint", "")).strip()
            if not fingerprint:
                continue
            generated_at = str(snapshot.get("generated_at", ""))
            _execute(connection, _upsert_pattern_memory_sql(), (fingerprint, generated_at, json.dumps(snapshot, ensure_ascii=False)))
        _execute(
            connection,
            """
            DELETE FROM pattern_memory_snapshots
            WHERE id NOT IN (
                SELECT id FROM pattern_memory_snapshots ORDER BY id DESC LIMIT 25
            )
            """
        )
        connection.commit()


def load_api_cache(cache_key: str, cache_date: str | None = None) -> dict[str, Any] | None:
    initialize_database()
    with _connect_database() as connection:
        if cache_date:
            row = _execute(
                connection,
                """
                SELECT cache_key, cache_date, payload_json, message, updated_at
                FROM api_cache
                WHERE cache_key = ? AND cache_date = ?
                """,
                (cache_key, cache_date),
            ).fetchone()
        else:
            row = _execute(
                connection,
                """
                SELECT cache_key, cache_date, payload_json, message, updated_at
                FROM api_cache
                WHERE cache_key = ?
                ORDER BY cache_date DESC, updated_at DESC
                LIMIT 1
                """,
                (cache_key,),
            ).fetchone()

    return _decode_api_cache_row(row)


def load_latest_api_cache(
    cache_key: str,
    *,
    before_date: str | None = None,
    payload_kind: str | None = None,
) -> dict[str, Any] | None:
    initialize_database()
    conditions = ["cache_key = ?"]
    params: list[Any] = [cache_key]
    if before_date:
        conditions.append("cache_date < ?")
        params.append(before_date)
    if payload_kind:
        conditions.append("payload_json::jsonb ->> 'kind' = ?" if using_postgres() else "json_extract(payload_json, '$.kind') = ?")
        params.append(payload_kind)

    with _connect_database() as connection:
        row = _execute(
            connection,
            f"""
            SELECT cache_key, cache_date, payload_json, message, updated_at
            FROM api_cache
            WHERE {" AND ".join(conditions)}
            ORDER BY cache_date DESC, updated_at DESC
            LIMIT 1
            """,
            params,
        ).fetchone()

    return _decode_api_cache_row(row)


def _decode_api_cache_row(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None

    try:
        payload = json.loads(row["payload_json"])
    except json.JSONDecodeError:
        payload = None

    return {
        "cache_key": row["cache_key"],
        "cache_date": row["cache_date"],
        "payload": payload,
        "message": row["message"],
        "updated_at": row["updated_at"],
    }


def save_api_cache(cache_key: str, cache_date: str, payload: Any, message: str = "") -> None:
    initialize_database()
    with _connect_database() as connection:
        _execute(connection, _upsert_api_cache_sql(), (cache_key, cache_date, json.dumps(payload, ensure_ascii=False), message))
        connection.commit()


def list_shorts_projects() -> list[dict[str, Any]]:
    initialize_database()
    with _connect_database() as connection:
        rows = _execute(
            connection,
            """
            SELECT id, title, updated_at, created_at
            FROM shorts_projects
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def load_shorts_project(project_id: str) -> dict[str, Any] | None:
    initialize_database()
    with _connect_database() as connection:
        row = _execute(
            connection,
            """
            SELECT id, title, payload_json, created_at, updated_at
            FROM shorts_projects
            WHERE id = ?
            """,
            (project_id,),
        ).fetchone()
    if row is None:
        return None
    try:
        payload = json.loads(row["payload_json"])
    except json.JSONDecodeError:
        payload = {}
    return {
        "id": row["id"],
        "title": row["title"],
        "payload": payload if isinstance(payload, dict) else {},
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def save_shorts_project(project: dict[str, Any]) -> dict[str, Any]:
    initialize_database()
    project_id = str(project.get("id") or uuid.uuid4().hex)
    title = str(project.get("title") or "Untitled Shorts Project").strip() or "Untitled Shorts Project"
    payload = project.get("payload", {})
    with _connect_database() as connection:
        _execute(
            connection,
            """
            INSERT INTO shorts_projects (id, title, payload_json)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (project_id, title, json.dumps(payload, ensure_ascii=False)),
        )
        connection.commit()
    saved = load_shorts_project(project_id)
    return saved or {"id": project_id, "title": title, "payload": payload, "created_at": "", "updated_at": ""}


def delete_shorts_project(project_id: str) -> None:
    initialize_database()
    with _connect_database() as connection:
        _execute(connection, "DELETE FROM shorts_projects WHERE id = ?", (project_id,))
        connection.commit()


def list_api_cache_rows(cache_key_prefix: str | None = None) -> list[dict[str, Any]]:
    initialize_database()
    with _connect_database() as connection:
        if cache_key_prefix:
            rows = _execute(
                connection,
                """
                SELECT cache_key, cache_date, payload_json, message, updated_at
                FROM api_cache
                WHERE cache_key LIKE ?
                ORDER BY cache_key, cache_date DESC, updated_at DESC
                """,
                (f"{cache_key_prefix}%",),
            ).fetchall()
        else:
            rows = _execute(
                connection,
                """
                SELECT cache_key, cache_date, payload_json, message, updated_at
                FROM api_cache
                ORDER BY cache_key, cache_date DESC, updated_at DESC
                """
            ).fetchall()

    decoded_rows: list[dict[str, Any]] = []
    for row in rows:
        decoded = _decode_api_cache_row(row)
        if decoded:
            decoded_rows.append(decoded)
    return decoded_rows


def _load_pattern_memory_from_json() -> dict[str, Any]:
    if not PATTERN_MEMORY_PATH.exists():
        return {"history": [], "latest": None}

    with PATTERN_MEMORY_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        return {"history": [], "latest": None}
    history = payload.get("history", [])
    latest = payload.get("latest")
    return {"history": history if isinstance(history, list) else [], "latest": latest}


def _migrate_json_pattern_memory_if_needed() -> None:
    with _connect_database() as connection:
        migrated = _execute(
            connection,
            "SELECT value_json FROM app_kv WHERE key = ?",
            ("pattern_memory_json_migrated",),
        ).fetchone()
        if migrated:
            return

        count = _row_value(_execute(connection, "SELECT COUNT(*) AS count FROM pattern_memory_snapshots").fetchone(), "count", 0)
        if count:
            _execute(connection, _upsert_app_kv_sql(), ("pattern_memory_json_migrated", "true"))
            connection.commit()
            return

        memory = _load_pattern_memory_from_json()
        history = memory.get("history", [])
        latest = memory.get("latest")
        snapshots = [item for item in history[-25:] if isinstance(item, dict)]
        if isinstance(latest, dict) and latest not in snapshots:
            snapshots.append(latest)

        for snapshot in snapshots[-25:]:
            fingerprint = str(snapshot.get("fingerprint", "")).strip()
            if not fingerprint:
                continue
            generated_at = str(snapshot.get("generated_at", ""))
            _execute(connection, _upsert_pattern_memory_sql(), (fingerprint, generated_at, json.dumps(snapshot, ensure_ascii=False)))
        _execute(connection, _upsert_app_kv_sql(), ("pattern_memory_json_migrated", "true"))
        connection.commit()


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
        "MODEL_NAME": str(values.get("MODEL_NAME", "google/gemma-4-e2b")),
        "MODEL_ENDPOINT": str(values.get("MODEL_ENDPOINT", "http://127.0.0.1:3010/v1")),
    }


def save_vault_settings(settings: dict[str, Any]) -> None:
    for key, value in settings.items():
        set_key(str(ENV_PATH), key, str(value))
