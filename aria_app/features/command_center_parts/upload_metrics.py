from __future__ import annotations

from datetime import date

import pandas as pd

def build_upload_takeaways(video_df: pd.DataFrame) -> dict[str, object]:
    empty_result: dict[str, object] = {
        "best": None,
        "weak": None,
        "pattern_rows": [],
        "improvement_rows": [],
    }
    if video_df is None or video_df.empty:
        return empty_result

    ranked = video_df.sort_values(["engagement_score", "views"], ascending=False).reset_index(drop=True)
    best = ranked.iloc[0]
    weak = ranked.iloc[-1]

    top_slice = ranked.head(min(8, len(ranked)))
    lower_slice = ranked.tail(min(8, len(ranked)))

    top_titles = " ".join(top_slice["title"].fillna("").astype(str).tolist()).lower()
    low_titles = " ".join(lower_slice["title"].fillna("").astype(str).tolist()).lower()

    pattern_rows: list[tuple[str, str]] = []
    improvement_rows: list[tuple[str, str]] = []

    if "male version" in top_titles:
        pattern_rows.append(("Packaging", "Male-version framing shows up in stronger uploads."))
    if "cover" in top_titles or "reimagined" in top_titles:
        pattern_rows.append(("Format", "Reimagined or cover framing appears in stronger uploads."))
    if top_slice["retention"].mean() >= lower_slice["retention"].mean():
        pattern_rows.append(("Retention", f"Top uploads average {top_slice['retention'].mean():.1f}% retention."))
    if top_slice["subscribers_gained"].fillna(0).sum() > 0:
        pattern_rows.append(("Subscriber Pull", f"Top uploads gained {int(top_slice['subscribers_gained'].fillna(0).sum())} subscribers in this window."))

    if lower_slice["retention"].mean() < top_slice["retention"].mean():
        improvement_rows.append(("Retention Gap", f"Lower performers trail by {(top_slice['retention'].mean() - lower_slice['retention'].mean()):.1f} retention points."))
    if lower_slice["watch_time_hours"].mean() < top_slice["watch_time_hours"].mean():
        improvement_rows.append(("Watch Time", "Weaker uploads hold less total watch time, which suggests less replay or weaker completion."))
    if "official audio" in low_titles:
        improvement_rows.append(("Packaging", "Plain utility-style titles look weaker than emotional or theatrical framing."))
    improvement_rows.append(("Next Move", "Model future titles on the best upload's framing, then test a sharper opening on the next release."))

    return {
        "best": best,
        "weak": weak,
        "pattern_rows": pattern_rows[:4],
        "improvement_rows": improvement_rows[:4],
    }


def assign_archetype_labels(title: str) -> list[str]:
    lowered = str(title).lower()
    labels: list[str] = []

    keyword_map = {
        "Hazbin": ["hazbin", "angel dust", "husk", "gravity"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Male Version": ["male version", "male cover"],
        "English Version": ["english version", "english ver", "english ver."],
        "Original": ["into the stars", "dreaming", "original song", "original music"],
        "Short-form Teaser": ["coming soon", "#shorts", "#viral"],
        "Cover": ["cover", "reimagined"],
        "Collaboration": ["ft.", "feat.", "with "],
        "Live / Session": ["live", "session", "acoustic"],
    }

    for label, keywords in keyword_map.items():
        if any(keyword in lowered for keyword in keywords):
            labels.append(label)

    if not labels:
        labels.append("General Performance")

    return labels


def _days_since_published(published_at: pd.Timestamp) -> int:
    if pd.isna(published_at):
        return 365
    published = pd.to_datetime(published_at, errors="coerce")
    if pd.isna(published):
        return 365
    if getattr(published, "tzinfo", None) is not None:
        published = published.tz_localize(None)
    today = pd.Timestamp(date.today())
    return max(int((today - published.normalize()).days), 0)


def assign_format_labels(title: str) -> list[str]:
    lowered = str(title).lower()
    labels: list[str] = []

    if any(keyword in lowered for keyword in ["coming soon", "#shorts", "#viral", "teaser", "snippet", "preview"]):
        labels.append("Short-form / Teaser")
    if any(keyword in lowered for keyword in ["ft.", "feat.", "with "]):
        labels.append("Collab Format")
    if any(keyword in lowered for keyword in ["live", "session", "acoustic"]):
        labels.append("Live Format")
    if any(keyword in lowered for keyword in ["cover", "reimagined", "english version", "male version"]):
        labels.append("Produced Cover")
    if "original" in lowered or any(keyword in lowered for keyword in ["into the stars", "dreaming"]):
        labels.append("Original Release")

    if not labels:
        labels.append("Standard Upload")

    return labels


def assign_franchise_label(title: str) -> str:
    lowered = str(title).lower()
    franchise_map = {
        "Hazbin Hotel": ["hazbin", "angel dust", "husk", "gravity", "losing streak", "brighter"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Original Universe": ["into the stars", "dreaming", "original"],
    }
    for label, keywords in franchise_map.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return "General / Mixed"


def build_archetype_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        labels = assign_archetype_labels(row.get("title", ""))
        for label in labels:
            grouped.setdefault(label, []).append(
                {
                    "views": float(row.get("views", 0) or 0),
                    "retention": float(row.get("retention", 0) or 0),
                    "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                    "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                    "engagement_score": float(row.get("engagement_score", 0) or 0),
                }
            )

    rows: list[dict[str, object]] = []
    for label, items in grouped.items():
        frame = pd.DataFrame(items)
        upload_count = len(frame)
        avg_views = frame["views"].mean()
        avg_retention = frame["retention"].mean()
        avg_watch_time = frame["watch_time_hours"].mean()
        total_subscribers = frame["subscribers_gained"].sum()
        avg_score = frame["engagement_score"].mean()
        momentum_score = round(float(avg_views * 0.35 + avg_retention * 10 + avg_watch_time * 2.5 + total_subscribers * 6 + avg_score * 0.15), 1)
        rows.append(
            {
                "archetype": label,
                "uploads": upload_count,
                "avg_views": round(float(avg_views), 1),
                "avg_retention": round(float(avg_retention), 2),
                "avg_watch_time_hours": round(float(avg_watch_time), 1),
                "total_subscribers": int(total_subscribers),
                "avg_engagement_score": round(float(avg_score), 1),
                "momentum_score": momentum_score,
            }
        )

    rows.sort(key=lambda row: (row["momentum_score"], row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_format_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        for label in assign_format_labels(row.get("title", "")):
            grouped.setdefault(label, []).append(
                {
                    "views": float(row.get("views", 0) or 0),
                    "retention": float(row.get("retention", 0) or 0),
                    "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                    "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                    "engagement_score": float(row.get("engagement_score", 0) or 0),
                }
            )

    rows: list[dict[str, object]] = []
    for label, items in grouped.items():
        frame = pd.DataFrame(items)
        rows.append(
            {
                "format": label,
                "uploads": int(len(frame)),
                "avg_views": round(float(frame["views"].mean()), 1),
                "avg_retention": round(float(frame["retention"].mean()), 2),
                "avg_engagement_score": round(float(frame["engagement_score"].mean()), 1),
                "total_subscribers": int(frame["subscribers_gained"].sum()),
            }
        )

    rows.sort(key=lambda row: (row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_franchise_heatmap_rows(video_df: pd.DataFrame) -> list[dict[str, object]]:
    if video_df is None or video_df.empty:
        return []

    grouped: dict[str, list[dict[str, float]]] = {}
    for _, row in video_df.iterrows():
        franchise = assign_franchise_label(row.get("title", ""))
        days_old = _days_since_published(row.get("published_at"))
        recency_weight = max(0.3, 1.35 - min(days_old, 365) / 365)
        grouped.setdefault(franchise, []).append(
            {
                "views": float(row.get("views", 0) or 0),
                "retention": float(row.get("retention", 0) or 0),
                "watch_time_hours": float(row.get("watch_time_hours", 0) or 0),
                "subscribers_gained": float(row.get("subscribers_gained", 0) or 0),
                "engagement_score": float(row.get("engagement_score", 0) or 0),
                "recency_weight": float(recency_weight),
            }
        )

    rows: list[dict[str, object]] = []
    for franchise, items in grouped.items():
        frame = pd.DataFrame(items)
        weighted_score = (
            (
                frame["views"] * 0.25
                + frame["retention"] * 12
                + frame["watch_time_hours"] * 2
                + frame["subscribers_gained"] * 8
                + frame["engagement_score"] * 0.18
            )
            * frame["recency_weight"]
        ).mean()
        rows.append(
            {
                "franchise": franchise,
                "uploads": int(len(frame)),
                "avg_views": round(float(frame["views"].mean()), 1),
                "avg_retention": round(float(frame["retention"].mean()), 2),
                "avg_engagement_score": round(float(frame["engagement_score"].mean()), 1),
                "recent_heat": round(float(weighted_score), 1),
                "recent_bias": round(float(frame["recency_weight"].mean()), 2),
                "total_subscribers": int(frame["subscribers_gained"].sum()),
            }
        )

    rows.sort(key=lambda row: (row["recent_heat"], row["avg_engagement_score"], row["avg_views"]), reverse=True)
    return rows


def build_archetype_recommendations(month_rows: list[dict[str, object]], global_rows: list[dict[str, object]]) -> list[tuple[str, str]]:
    recommendations: list[tuple[str, str]] = []

    if month_rows:
        top_month = month_rows[0]
        recommendations.append(
            (
                "Current Winner",
                f"{top_month['archetype']} is the strongest current lane with momentum score {top_month['momentum_score']:.1f}.",
            )
        )

    if global_rows:
        top_global = global_rows[0]
        recommendations.append(
            (
                "Reliable Across Window",
                f"{top_global['archetype']} looks strongest across the broader upload history, not just this month.",
            )
        )

    month_labels = {row["archetype"] for row in month_rows[:4]}
    global_labels = {row["archetype"] for row in global_rows[:4]}
    overlap = [label for label in month_labels if label in global_labels]
    if overlap:
        recommendations.append(
            (
                "Repeatable Lane",
                f"{overlap[0]} is showing both short-term and broader strength, which makes it a safer momentum play.",
            )
        )

    if month_rows:
        high_retention = sorted(month_rows, key=lambda row: row["avg_retention"], reverse=True)[0]
        if high_retention["archetype"] != month_rows[0]["archetype"]:
            recommendations.append(
                (
                    "High-Retention Wildcard",
                    f"{high_retention['archetype']} keeps viewers well. It could be a strong creative pivot if packaged better.",
                )
            )

    return recommendations[:4]


def build_heatmap_recommendations(
    franchise_rows: list[dict[str, object]],
    format_rows: list[dict[str, object]],
) -> list[tuple[str, str]]:
    recommendations: list[tuple[str, str]] = []

    if franchise_rows:
        hottest = franchise_rows[0]
        recommendations.append(
            (
                "Hottest Franchise",
                f"{hottest['franchise']} is carrying the strongest recent heat at {hottest['recent_heat']:.1f}.",
            )
        )

    if len(franchise_rows) > 1:
        runner_up = franchise_rows[1]
        recommendations.append(
            (
                "Second Best Bet",
                f"{runner_up['franchise']} is the next-closest momentum lane and worth keeping warm.",
            )
        )

    if format_rows:
        best_format = format_rows[0]
        recommendations.append(
            (
                "Best Format",
                f"{best_format['format']} currently looks strongest by engagement and views.",
            )
        )

    high_retention_franchise = None
    if franchise_rows:
        high_retention_franchise = sorted(franchise_rows, key=lambda row: row["avg_retention"], reverse=True)[0]
    if high_retention_franchise and high_retention_franchise["franchise"] != franchise_rows[0]["franchise"]:
        recommendations.append(
            (
                "Retention Wildcard",
                f"{high_retention_franchise['franchise']} holds attention especially well and may deserve better packaging.",
            )
        )

    return recommendations[:4]


def build_request_signal_rows(request_text: str) -> list[dict[str, object]]:
    if not request_text.strip():
        return []

    request_patterns = {
        "Hazbin Hotel": ["hazbin", "angel dust", "husk", "gravity", "losing streak", "brighter"],
        "Epic / Ilium": ["epic", "ilium", "troy", "odysseus", "athena", "fire", "pride of troy"],
        "K-Pop Demon Hunters": ["kpop demon hunters", "saja boys", "your idol", "soda pop"],
        "Male Version": ["male version", "male cover"],
        "English Version": ["english version", "english ver", "english"],
        "Original": ["original", "into the stars", "dreaming"],
    }

    lowered = request_text.lower()
    rows: list[dict[str, object]] = []
    for label, keywords in request_patterns.items():
        count = sum(lowered.count(keyword) for keyword in keywords)
        if count > 0:
            rows.append({"signal": label, "mentions": count})

    rows.sort(key=lambda row: row["mentions"], reverse=True)
    return rows


def build_gap_rows(monthly_df: pd.DataFrame, global_franchises: list[dict[str, object]]) -> list[dict[str, object]]:
    if not global_franchises:
        return []

    month_titles = " ".join(monthly_df["title"].fillna("").astype(str).tolist()).lower() if monthly_df is not None and not monthly_df.empty else ""
    rows: list[dict[str, object]] = []
    for row in global_franchises[:6]:
        franchise = str(row["franchise"])
        if franchise == "Hazbin Hotel":
            active = "hazbin" in month_titles
        elif franchise == "Epic / Ilium":
            active = any(keyword in month_titles for keyword in ["epic", "ilium", "troy", "fire"])
        elif franchise == "K-Pop Demon Hunters":
            active = any(keyword in month_titles for keyword in ["kpop demon hunters", "saja boys", "your idol", "soda pop"])
        elif franchise == "Original Universe":
            active = any(keyword in month_titles for keyword in ["into the stars", "dreaming", "original"])
        else:
            active = True

        if not active:
            rows.append(
                {
                    "franchise": franchise,
                    "recent_heat": row["recent_heat"],
                    "gap_note": f"{franchise} is strong in the broader window but missing from the selected month.",
                }
            )

    rows.sort(key=lambda row: row["recent_heat"], reverse=True)
    return rows
