from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

try:
    import psycopg
except ModuleNotFoundError:
    psycopg = None

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import storage

SQLITE_PATH = BASE_DIR / "data" / "studio.db"


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}").fetchall()]


def _upsert_app_kv(pg: psycopg.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        pg.execute(
            """
            INSERT INTO app_kv (key, value_json, updated_at)
            VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
            ON CONFLICT(key) DO UPDATE SET
                value_json = excluded.value_json,
                updated_at = excluded.updated_at
            """,
            (row["key"], row["value_json"], row.get("updated_at")),
        )


def _copy_calendar(pg: psycopg.Connection, rows: list[dict[str, Any]]) -> None:
    pg.execute("DELETE FROM content_calendar")
    for row in rows:
        pg.execute(
            """
            INSERT INTO content_calendar (
                sort_order, title, stage, priority, content_pillar, target_upload_date, notes, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
            """,
            (
                row.get("sort_order", 0),
                row.get("title", ""),
                row.get("stage", "Song Idea"),
                row.get("priority", "Medium"),
                row.get("content_pillar", ""),
                row.get("target_upload_date", ""),
                row.get("notes", ""),
                row.get("updated_at"),
            ),
        )


def _upsert_pattern_memory(pg: psycopg.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        pg.execute(
            """
            INSERT INTO pattern_memory_snapshots (fingerprint, generated_at, snapshot_json, created_at)
            VALUES (%s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
            ON CONFLICT(fingerprint) DO UPDATE SET
                generated_at = excluded.generated_at,
                snapshot_json = excluded.snapshot_json
            """,
            (row["fingerprint"], row["generated_at"], row["snapshot_json"], row.get("created_at")),
        )


def _upsert_api_cache(pg: psycopg.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        pg.execute(
            """
            INSERT INTO api_cache (cache_key, cache_date, payload_json, message, created_at, updated_at)
            VALUES (%s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), COALESCE(%s, CURRENT_TIMESTAMP))
            ON CONFLICT(cache_key, cache_date) DO UPDATE SET
                payload_json = excluded.payload_json,
                message = excluded.message,
                updated_at = excluded.updated_at
            """,
            (
                row["cache_key"],
                row["cache_date"],
                row["payload_json"],
                row.get("message", ""),
                row.get("created_at"),
                row.get("updated_at"),
            ),
        )


def _upsert_shorts_projects(pg: psycopg.Connection, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        pg.execute(
            """
            INSERT INTO shorts_projects (id, title, payload_json, created_at, updated_at)
            VALUES (%s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP), COALESCE(%s, CURRENT_TIMESTAMP))
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                row["id"],
                row.get("title", ""),
                row["payload_json"],
                row.get("created_at"),
                row.get("updated_at"),
            ),
        )


def main() -> None:
    if psycopg is None:
        raise SystemExit("psycopg is not installed. Run pip install -r requirements.txt after PostgreSQL is installed, then rerun this migration.")
    database_url = os.environ.get("DATABASE_URL") or storage._database_url()
    if not database_url:
        raise SystemExit("Set DATABASE_URL in .env or the environment before running this migration.")
    if not SQLITE_PATH.exists():
        raise SystemExit(f"SQLite database not found: {SQLITE_PATH}")

    storage.initialize_database()

    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row
    try:
        with psycopg.connect(database_url) as pg:
            _copy_calendar(pg, _rows(sqlite, "content_calendar"))
            _upsert_pattern_memory(pg, _rows(sqlite, "pattern_memory_snapshots"))
            _upsert_app_kv(pg, _rows(sqlite, "app_kv"))
            _upsert_api_cache(pg, _rows(sqlite, "api_cache"))
            _upsert_shorts_projects(pg, _rows(sqlite, "shorts_projects"))
            pg.commit()
    finally:
        sqlite.close()

    print("SQLite data migrated to PostgreSQL.")


if __name__ == "__main__":
    main()
