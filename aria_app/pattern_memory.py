from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

import pandas as pd

from storage import load_pattern_memory, save_pattern_memory


WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "into",
    "than",
    "male",
    "version",
    "cover",
    "song",
    "video",
    "official",
    "live",
    "music",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "or",
}


def _safe_calendar_frame(calendar_df: pd.DataFrame) -> pd.DataFrame:
    if calendar_df is None or calendar_df.empty:
        return pd.DataFrame(columns=["title", "stage", "priority", "content_pillar", "target_upload_date", "notes"])
    frame = calendar_df.copy()
    for column in ["title", "stage", "priority", "content_pillar", "notes"]:
        if column not in frame.columns:
            frame[column] = ""
        frame[column] = frame[column].fillna("").astype(str)
    if "target_upload_date" not in frame.columns:
        frame["target_upload_date"] = pd.NaT
    frame["target_upload_date"] = pd.to_datetime(frame["target_upload_date"], errors="coerce")
    return frame


def _safe_analytics_frame(analytics_df: pd.DataFrame) -> pd.DataFrame:
    if analytics_df is None or analytics_df.empty:
        return pd.DataFrame(columns=["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained"])
    frame = analytics_df.copy()
    if "date" not in frame.columns:
        frame["date"] = pd.NaT
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ["views", "ctr", "retention", "watch_time_hours", "subscribers_gained"]:
        if column not in frame.columns:
            frame[column] = pd.NA
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _extract_title_patterns(titles: list[str]) -> list[dict[str, Any]]:
    words: list[str] = []
    phrases: dict[str, int] = {}
    for title in titles:
        lowered = title.lower()
        title_words = [word for word in re.findall(r"[a-z0-9']+", lowered) if len(word) > 2 and word not in STOP_WORDS]
        words.extend(title_words)
        for size in (2, 3):
            for index in range(len(title_words) - size + 1):
                phrase = " ".join(title_words[index : index + size])
                phrases[phrase] = phrases.get(phrase, 0) + 1

    word_counts = pd.Series(words).value_counts().head(6) if words else pd.Series(dtype="int64")
    results: list[dict[str, Any]] = []
    for keyword, count in word_counts.items():
        results.append({"pattern": keyword, "type": "keyword", "count": int(count)})

    for phrase, count in sorted(phrases.items(), key=lambda item: (-item[1], item[0]))[:4]:
        results.append({"pattern": phrase, "type": "phrase", "count": int(count)})

    return results[:8]


def _build_publish_memory(analytics_df: pd.DataFrame) -> dict[str, Any]:
    if analytics_df.empty or analytics_df["date"].isna().all():
        return {
            "best_day": "No live data",
            "best_score": None,
            "weak_day": "No live data",
            "weak_score": None,
            "weekday_rows": [],
        }

    timing_df = analytics_df.dropna(subset=["date"]).copy()
    timing_df["weekday"] = timing_df["date"].dt.day_name()
    grouped = (
        timing_df.groupby("weekday", dropna=False)
        .agg(avg_views=("views", "mean"), avg_retention=("retention", "mean"), avg_watch_time=("watch_time_hours", "mean"))
        .reset_index()
    )
    grouped["weekday"] = pd.Categorical(grouped["weekday"], categories=WEEKDAY_ORDER, ordered=True)
    grouped = grouped.sort_values("weekday")
    grouped["publish_score"] = (grouped["avg_views"].fillna(0) * 0.5 + grouped["avg_retention"].fillna(0) * 8 + grouped["avg_watch_time"].fillna(0) * 4).round(1)
    if grouped.empty:
        return {
            "best_day": "No live data",
            "best_score": None,
            "weak_day": "No live data",
            "weak_score": None,
            "weekday_rows": [],
        }

    best_row = grouped.sort_values("publish_score", ascending=False).iloc[0]
    weak_row = grouped.sort_values("publish_score", ascending=True).iloc[0]
    weekday_rows = []
    for _, row in grouped.iterrows():
        weekday_rows.append(
            {
                "weekday": str(row["weekday"]),
                "avg_views": round(float(row["avg_views"]), 1) if pd.notna(row["avg_views"]) else None,
                "avg_retention": round(float(row["avg_retention"]), 2) if pd.notna(row["avg_retention"]) else None,
                "publish_score": round(float(row["publish_score"]), 1) if pd.notna(row["publish_score"]) else None,
            }
        )

    return {
        "best_day": str(best_row["weekday"]),
        "best_score": round(float(best_row["publish_score"]), 1),
        "weak_day": str(weak_row["weekday"]),
        "weak_score": round(float(weak_row["publish_score"]), 1),
        "weekday_rows": weekday_rows,
    }


def _build_stage_memory(calendar_df: pd.DataFrame) -> dict[str, Any]:
    if calendar_df.empty:
        return {
            "bottleneck_stage": "No repertoire data",
            "bottleneck_count": 0,
            "overdue_count": 0,
            "stage_rows": [],
        }

    stage_counts = calendar_df["stage"].value_counts()
    bottleneck_stage = stage_counts.idxmax() if not stage_counts.empty else "No repertoire data"
    bottleneck_count = int(stage_counts.max()) if not stage_counts.empty else 0
    today = pd.Timestamp.today().normalize()
    overdue_mask = calendar_df["target_upload_date"].notna() & (calendar_df["target_upload_date"] < today) & (calendar_df["stage"] != "Upload")
    overdue_count = int(overdue_mask.sum())
    stage_rows = [{"stage": str(stage), "count": int(count)} for stage, count in stage_counts.items()]
    return {
        "bottleneck_stage": str(bottleneck_stage),
        "bottleneck_count": bottleneck_count,
        "overdue_count": overdue_count,
        "stage_rows": stage_rows,
    }


def _build_pillar_memory(calendar_df: pd.DataFrame) -> list[dict[str, Any]]:
    if calendar_df.empty:
        return []
    pillar_counts = (
        calendar_df["content_pillar"]
        .replace("", pd.NA)
        .dropna()
        .astype(str)
        .value_counts()
        .head(5)
    )
    return [{"pillar": pillar, "count": int(count)} for pillar, count in pillar_counts.items()]


def _build_repeat_and_reduce(snapshot: dict[str, Any]) -> tuple[list[str], list[str]]:
    repeat: list[str] = []
    reduce: list[str] = []

    publish = snapshot["publish_memory"]
    stage = snapshot["stage_memory"]
    pillars = snapshot["pillar_memory"]
    patterns = snapshot["title_patterns"]

    if publish["best_score"] is not None:
        repeat.append(f"Prioritize stronger uploads for {publish['best_day']}, your current best-performing weekday.")
    if pillars:
        repeat.append(f"Keep leaning into {pillars[0]['pillar']}, which appears most often in your active repertoire.")
    if patterns:
        repeat.append(f"Reuse the framing around '{patterns[0]['pattern']}' when it fits naturally.")
    if stage["bottleneck_stage"] not in {"No repertoire data", "Upload"}:
        reduce.append(f"Too many songs are stuck in {stage['bottleneck_stage']}; clear that lane before adding more ideas.")
    if stage["overdue_count"] > 0:
        reduce.append(f"{stage['overdue_count']} repertoire items are overdue, so tighten scheduling before expanding the slate.")
    if publish["weak_score"] is not None:
        reduce.append(f"Treat {publish['weak_day']} as a weaker release day unless the upload is especially strong.")

    return repeat[:3], reduce[:3]


def build_pattern_memory_snapshot(
    analytics_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    niche_output: str = "",
) -> dict[str, Any]:
    safe_analytics = _safe_analytics_frame(analytics_df)
    safe_calendar = _safe_calendar_frame(calendar_df)
    titles = [title for title in safe_calendar["title"].tolist() if title.strip()]
    title_patterns = _extract_title_patterns(titles)
    publish_memory = _build_publish_memory(safe_analytics)
    stage_memory = _build_stage_memory(safe_calendar)
    pillar_memory = _build_pillar_memory(safe_calendar)
    fingerprint_source = (
        safe_analytics.fillna("").to_csv(index=False)
        + safe_calendar.fillna("").to_csv(index=False)
        + niche_output.strip()
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
    snapshot = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "fingerprint": fingerprint,
        "title_patterns": title_patterns,
        "publish_memory": publish_memory,
        "stage_memory": stage_memory,
        "pillar_memory": pillar_memory,
        "niche_hint": niche_output.strip().splitlines()[0][:140] if niche_output.strip() else "",
    }
    repeat, reduce = _build_repeat_and_reduce(snapshot)
    snapshot["repeat_more"] = repeat
    snapshot["reduce_or_fix"] = reduce
    return snapshot


def refresh_pattern_memory(
    analytics_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    niche_output: str = "",
) -> dict[str, Any]:
    memory = load_pattern_memory()
    snapshot = build_pattern_memory_snapshot(analytics_df, calendar_df, niche_output)
    latest = memory.get("latest")
    if latest and latest.get("fingerprint") == snapshot["fingerprint"]:
        return memory

    history = memory.get("history", [])
    history.append(snapshot)
    memory = {"history": history[-25:], "latest": snapshot}
    save_pattern_memory(memory)
    return memory
