"""Normalized YouTube Live Chat Message Event."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from events.base_event import BaseEvent


@dataclass
class ChatMessageEvent(BaseEvent):
    """Normalized chat message event representing a live stream comment."""

    message_id: str = ""
    author_id: str = ""
    author_name: str = "Unknown"
    text: str = ""
    clean_text: str = ""
    published_at: str = ""
    is_owner: bool = False
    is_moderator: bool = False
    is_sponsor: bool = False
    detected_language: str = "unknown"
    raw_item: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_youtube_item(cls, item: Dict[str, Any]) -> Optional["ChatMessageEvent"]:
        """Parse raw YouTube Data API liveChatMessage item into normalized ChatMessageEvent."""
        message_id = item.get("id")
        if not message_id:
            return None

        author_details = item.get("authorDetails", {})
        snippet = item.get("snippet", {})

        author_id = author_details.get("channelId", "")
        author_name = author_details.get("displayName", "Unknown")
        is_owner = author_details.get("isChatOwner", False)
        is_moderator = author_details.get("isChatModerator", False)
        is_sponsor = author_details.get("isChatSponsor", False)

        display_message = snippet.get("displayMessage", "").strip()
        published_at = snippet.get("publishedAt", "")

        return cls(
            message_id=message_id,
            author_id=author_id,
            author_name=author_name,
            text=display_message,
            clean_text=display_message,
            published_at=published_at,
            is_owner=is_owner,
            is_moderator=is_moderator,
            is_sponsor=is_sponsor,
            raw_item=item,
        )
