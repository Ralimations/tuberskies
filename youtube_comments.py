from __future__ import annotations

from typing import Any

from googleapiclient.errors import HttpError

from youtube_auth import _authorized_youtube_client


def list_recent_comment_threads(
    settings: dict[str, str],
    video_id: str = "",
    max_results: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    youtube_client, error_message = _authorized_youtube_client(settings)
    if youtube_client is None:
        return [], error_message or "YouTube authorization is not ready yet."

    try:
        channel_response = youtube_client.channels().list(part="id", mine=True).execute()
        channel_items = channel_response.get("items", [])
        if not channel_items:
            return [], "Google authorization succeeded, but no YouTube channel was returned for this account."
        channel_id = channel_items[0].get("id", "")

        request_kwargs: dict[str, Any] = {
            "part": "snippet,replies",
            "maxResults": min(max(max_results, 1), 50),
            "order": "time",
            "textFormat": "plainText",
        }
        if video_id.strip():
            request_kwargs["videoId"] = video_id.strip()
        else:
            request_kwargs["allThreadsRelatedToChannelId"] = channel_id

        response = youtube_client.commentThreads().list(**request_kwargs).execute()
        rows: list[dict[str, Any]] = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            top_comment = snippet.get("topLevelComment", {})
            comment_snippet = top_comment.get("snippet", {})
            replies = item.get("replies", {}).get("comments", [])
            already_replied = any(
                reply.get("snippet", {}).get("authorChannelId", {}).get("value") == channel_id
                for reply in replies
            )
            rows.append(
                {
                    "thread_id": item.get("id", ""),
                    "comment_id": top_comment.get("id", ""),
                    "video_id": snippet.get("videoId", ""),
                    "author": comment_snippet.get("authorDisplayName", "Unknown"),
                    "text": comment_snippet.get("textOriginal") or comment_snippet.get("textDisplay", ""),
                    "published_at": comment_snippet.get("publishedAt", ""),
                    "like_count": comment_snippet.get("likeCount", 0),
                    "reply_count": snippet.get("totalReplyCount", 0),
                    "can_reply": bool(snippet.get("canReply", False)),
                    "already_replied": already_replied,
                }
            )
        return rows, "Loaded recent YouTube comments."
    except HttpError as error:
        return [], f"YouTube Data API error while loading comments: {error}"
    except Exception as error:  # pragma: no cover
        return [], f"Unexpected error while loading comments: {error}"


def reply_to_comment(settings: dict[str, str], parent_comment_id: str, reply_text: str) -> tuple[bool, str]:
    parent_comment_id = parent_comment_id.strip()
    reply_text = reply_text.strip()
    if not parent_comment_id:
        return False, "Choose a comment first."
    if not reply_text:
        return False, "Reply text cannot be empty."
    if len(reply_text) > 900:
        return False, "Keep replies under 900 characters for safety and readability."

    youtube_client, error_message = _authorized_youtube_client(settings)
    if youtube_client is None:
        return False, error_message or "YouTube authorization is not ready yet."

    try:
        youtube_client.comments().insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": parent_comment_id,
                    "textOriginal": reply_text,
                }
            },
        ).execute()
        return True, "Reply posted to YouTube."
    except HttpError as error:
        return False, f"YouTube Data API error while posting reply: {error}"
    except Exception as error:  # pragma: no cover
        return False, f"Unexpected error while posting reply: {error}"
