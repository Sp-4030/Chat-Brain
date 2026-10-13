"""YouTube Live Chat Message Sender.

Posts AI generated text responses back to YouTube Live Chat,
enforcing length boundaries and handling quota and rate-limit errors.
"""

from __future__ import annotations

from typing import Optional
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from config.settings import Settings, get_settings
from utils.logger import get_logger

logger = get_logger("MessageSender")


class YouTubeMessageSender:
    """Handles sending text replies to YouTube Live Chat."""

    def __init__(self, service: Resource, settings: Optional[Settings] = None) -> None:
        self.service = service
        self.settings = settings or get_settings()

    def send_reply(self, live_chat_id: str, reply_text: str) -> Optional[str]:
        """Post a text response to the specified liveChatId.

        Returns:
            The inserted message ID on success, or None on failure.
        """
        if not live_chat_id or not reply_text:
            return None

        # Truncate to maximum reply length safety limit
        max_len = self.settings.MAX_REPLY_LENGTH
        if len(reply_text) > max_len:
            shortened = reply_text[: max_len - 3]
            if " " in shortened:
                shortened = shortened.rsplit(" ", 1)[0]
            reply_text = shortened + "..."

        try:
            body = {
                "snippet": {
                    "liveChatId": live_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": reply_text,
                    },
                }
            }
            response = self.service.liveChatMessages().insert(
                part="snippet",
                body=body,
            ).execute()

            message_id = response.get("id")
            logger.info("Successfully posted reply to YouTube (ID: %s)", message_id)
            return message_id

        except HttpError as err:
            if "quotaExceeded" in str(err):
                logger.error("YouTube API quota exceeded while sending message: %s", err)
            else:
                logger.error("HTTP error posting reply to YouTube: %s", err)
            return None
        except Exception as err:
            logger.error("Unexpected error posting reply: %s", err)
            return None
