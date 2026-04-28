from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_auth import _require_authorized_credentials, build_youtube_data_client


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
        for column in ["views", "estimatedMinutesWatched", "subscribersGained", "averageViewPercentage"]:
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
        frame["has_watch_minutes"] = frame["estimated_minutes_watched"].notna()
        frame = frame[["date", "views", "ctr", "retention", "watch_time_hours", "subscribers_gained", "has_watch_minutes"]]

        full_range = pd.DataFrame({"date": pd.date_range(start=start_date, end=end_date, freq="D")})
        frame = full_range.merge(frame, on="date", how="left").sort_values("date")
        frame["views"] = frame["views"].fillna(0)
        frame["retention"] = frame["retention"].ffill()
        frame["watch_time_hours"] = frame["watch_time_hours"].where(frame["has_watch_minutes"].fillna(False), pd.NA)
        frame["subscribers_gained"] = frame["subscribers_gained"].fillna(0)
        frame = frame.drop(columns=["has_watch_minutes"])

        channel_title = channel_items[0].get("snippet", {}).get("title", "your YouTube channel")
        return frame, f"Live analytics loaded for {channel_title}."
    except HttpError as error:
        return None, f"YouTube Analytics API error: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while loading live analytics: {error}"


def load_video_performance(settings: dict[str, str], days: int = 365, max_results: int = 100) -> tuple[pd.DataFrame | None, str]:
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
            dimensions="video",
            sort="-views",
            maxResults=max_results,
        ).execute()

        headers = [header["name"] for header in analytics_response.get("columnHeaders", [])]
        rows = analytics_response.get("rows", [])
        if not headers or not rows:
            return None, "The YouTube Analytics API returned no video-level rows for this date range."

        frame = pd.DataFrame(rows, columns=headers)
        for column in ["views", "estimatedMinutesWatched", "subscribersGained", "averageViewPercentage"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

        video_ids = [video_id for video_id in frame["video"].dropna().astype(str).tolist() if video_id.strip()]
        video_lookup: dict[str, dict[str, Any]] = {}
        for index in range(0, len(video_ids), 50):
            batch_ids = video_ids[index : index + 50]
            details_response = youtube_client.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch_ids),
            ).execute()
            for item in details_response.get("items", []):
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                video_lookup[item.get("id", "")] = {
                    "title": snippet.get("title", "Untitled Video"),
                    "published_at": snippet.get("publishedAt", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "like_count": pd.to_numeric(statistics.get("likeCount"), errors="coerce"),
                    "comment_count": pd.to_numeric(statistics.get("commentCount"), errors="coerce"),
                }

        frame["video_id"] = frame["video"].astype(str)
        frame["title"] = frame["video_id"].map(lambda value: video_lookup.get(value, {}).get("title", "Untitled Video"))
        frame["published_at"] = pd.to_datetime(
            frame["video_id"].map(lambda value: video_lookup.get(value, {}).get("published_at", "")),
            errors="coerce",
        )
        frame["like_count"] = frame["video_id"].map(lambda value: video_lookup.get(value, {}).get("like_count"))
        frame["comment_count"] = frame["video_id"].map(lambda value: video_lookup.get(value, {}).get("comment_count"))
        frame["retention"] = frame["averageViewPercentage"]
        frame["watch_time_hours"] = frame["estimatedMinutesWatched"].fillna(0) / 60
        frame["subscribers_gained"] = frame["subscribersGained"]
        frame["engagement_score"] = (
            frame["views"].fillna(0) * 0.45
            + frame["watch_time_hours"].fillna(0) * 3.5
            + frame["retention"].fillna(0) * 8
            + frame["subscribers_gained"].fillna(0) * 12
            + frame["comment_count"].fillna(0) * 2
            + frame["like_count"].fillna(0) * 0.3
        ).round(1)
        frame = frame.sort_values(["engagement_score", "views"], ascending=False).reset_index(drop=True)
        frame = frame[
            [
                "video_id",
                "title",
                "published_at",
                "views",
                "retention",
                "watch_time_hours",
                "subscribers_gained",
                "like_count",
                "comment_count",
                "engagement_score",
            ]
        ]

        channel_title = channel_items[0].get("snippet", {}).get("title", "your YouTube channel")
        return frame, f"Upload performance loaded for {channel_title}."
    except HttpError as error:
        return None, f"YouTube Analytics API error while loading upload performance: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while loading upload performance: {error}"


def search_music_trends(settings: dict[str, str], queries: list[str], max_results_per_query: int = 4) -> tuple[pd.DataFrame | None, str]:
    try:
        youtube_client = build_youtube_data_client(settings)
    except Exception as error:
        return None, f"Trend search is unavailable: {error}"

    cleaned_queries = [query.strip() for query in queries if query and query.strip()]
    if not cleaned_queries:
        return None, "Trend search needs at least one query."

    published_after = (date.today() - timedelta(days=120)).isoformat() + "T00:00:00Z"
    rows: list[dict[str, Any]] = []

    try:
        for query in cleaned_queries[:4]:
            response = youtube_client.search().list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                maxResults=max_results_per_query,
                publishedAfter=published_after,
                topicId="/m/04rlf",
                videoCategoryId="10",
                regionCode="US",
            ).execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                rows.append(
                    {
                        "query": query,
                        "title": snippet.get("title", "Untitled"),
                        "channel_title": snippet.get("channelTitle", ""),
                        "published_at": pd.to_datetime(snippet.get("publishedAt", ""), errors="coerce"),
                        "video_id": video_id,
                        "video_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                    }
                )

        if not rows:
            return None, "No related trend videos were returned for the current niche queries."

        frame = pd.DataFrame(rows).drop_duplicates(subset=["video_id", "title"]).reset_index(drop=True)
        return frame, "Trend search loaded from YouTube."
    except HttpError as error:
        return None, f"YouTube Data API error while searching trend videos: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while searching trend videos: {error}"
