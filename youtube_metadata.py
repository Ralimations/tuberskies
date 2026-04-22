from __future__ import annotations

from typing import Any

from googleapiclient.errors import HttpError

from youtube_auth import _authorized_youtube_client


def get_owned_video_metadata(settings: dict[str, str], video_id: str) -> tuple[dict[str, Any] | None, str]:
    video_id = video_id.strip()
    if not video_id:
        return None, "Choose a video first."

    youtube_client, error_message = _authorized_youtube_client(settings)
    if youtube_client is None:
        return None, error_message or "YouTube authorization is not ready yet."

    try:
        response = youtube_client.videos().list(part="snippet,status", id=video_id).execute()
        items = response.get("items", [])
        if not items:
            return None, "YouTube did not return that video. It may not belong to the authorized channel."

        item = items[0]
        snippet = item.get("snippet", {})
        status = item.get("status", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("maxres", {}).get("url")
            or thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url", "")
        )
        return {
            "video_id": item.get("id", video_id),
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "tags": snippet.get("tags", []),
            "category_id": snippet.get("categoryId", "10"),
            "thumbnail_url": thumbnail_url,
            "privacy_status": status.get("privacyStatus", ""),
        }, "Loaded current video metadata."
    except HttpError as error:
        return None, f"YouTube Data API error while loading video metadata: {error}"
    except Exception as error:  # pragma: no cover
        return None, f"Unexpected error while loading video metadata: {error}"


def update_owned_video_metadata(
    settings: dict[str, str],
    video_id: str,
    title: str,
    description: str,
    tags: list[str],
) -> tuple[bool, str]:
    current, message = get_owned_video_metadata(settings, video_id)
    if current is None:
        return False, message

    safe_title = title.strip()
    safe_description = description.strip()
    safe_tags = [tag.strip() for tag in tags if tag and tag.strip()]
    deduped_tags: list[str] = []
    for tag in safe_tags:
        if tag.lower() not in {item.lower() for item in deduped_tags}:
            deduped_tags.append(tag)

    if not safe_title:
        return False, "Title cannot be empty."
    if len(safe_title) > 100:
        return False, "YouTube titles must be 100 characters or fewer."
    if len(safe_description.encode("utf-8")) > 5000:
        return False, "YouTube descriptions must be 5000 bytes or fewer."
    tag_char_count = sum(len(tag) for tag in deduped_tags) + max(len(deduped_tags) - 1, 0)
    if tag_char_count > 500:
        return False, "YouTube tag metadata is limited to roughly 500 characters including separators."

    youtube_client, error_message = _authorized_youtube_client(settings)
    if youtube_client is None:
        return False, error_message or "YouTube authorization is not ready yet."

    try:
        youtube_client.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": safe_title,
                    "description": safe_description,
                    "tags": deduped_tags,
                    "categoryId": current.get("category_id", "10"),
                },
            },
        ).execute()
        return True, "Video metadata updated on YouTube."
    except HttpError as error:
        return False, f"YouTube Data API error while updating metadata: {error}"
    except Exception as error:  # pragma: no cover
        return False, f"Unexpected error while updating metadata: {error}"
