"""YouTube Live Chat Reader.

Identifies active live streams, retrieves incoming messages, handles pagination tokens,
and calculates YouTube-mandated polling intervals.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from config.settings import Settings, get_settings
from events.chat_message_event import ChatMessageEvent
from utils.logger import get_logger

logger = get_logger("LiveChatReader")


class LiveChatReader:
    """Reads messages from YouTube Live Chat with quota-awareness."""

    def __init__(self, service: Resource, settings: Optional[Settings] = None) -> None:
        self.service = service
        self.settings = settings or get_settings()
        self.live_chat_id: Optional[str] = None
        self.active_broadcast_title: Optional[str] = None
        self.next_page_token: Optional[str] = None

    def find_active_live_chat_id(self) -> Optional[str]:
        """Query active live broadcasts to find liveChatId."""
        logger.info("Searching for active YouTube Live broadcasts...")
        try:
            response = self.service.liveBroadcasts().list(
                part="snippet,status",
                mine=True,
                maxResults=10,
            ).execute()

            items = response.get("items", [])
            for item in items:
                status = item.get("status", {})
                snippet = item.get("snippet", {})
                life_cycle = status.get("lifeCycleStatus")
                chat_id = snippet.get("liveChatId")

                if life_cycle == "live" and chat_id:
                    self.live_chat_id = chat_id
                    self.active_broadcast_title = snippet.get("title", "Untitled Live")
                    logger.info(
                        "Found active live broadcast: '%s' (Chat ID: %s)",
                        self.active_broadcast_title,
                        chat_id,
                    )
                    return chat_id

            logger.warning("No active live stream found with status 'live'.")
            return None

        except HttpError as err:
            if "quotaExceeded" in str(err):
                logger.error("YouTube daily quota is exhausted during broadcast discovery.")
            else:
                logger.error("YouTube API error while checking broadcasts: %s", err)
            return None
        except Exception as err:
            logger.error("Unexpected error searching for live broadcasts: %s", err)
            return None

    def fetch_messages(self) -> Tuple[List[ChatMessageEvent], float]:
        """Fetch incoming live chat messages.

        Returns:
            Tuple of (list_of_events, recommended_sleep_seconds).
        """
        if not self.live_chat_id:
            return [], self.settings.ERROR_RETRY_SECONDS

        params: Dict[str, Any] = {
            "liveChatId": self.live_chat_id,
            "part": "snippet,authorDetails",
        }
        if self.next_page_token:
            params["pageToken"] = self.next_page_token

        try:
            response = self.service.liveChatMessages().list(**params).execute()

            self.next_page_token = response.get("nextPageToken")
            raw_items = response.get("items", [])

            events: List[ChatMessageEvent] = []
            for item in raw_items:
                event = ChatMessageEvent.from_youtube_item(item)
                if event:
                    events.append(event)

            # Polling interval recommended by YouTube
            polling_millis = response.get(
                "pollingIntervalMillis",
                self.settings.DEFAULT_POLL_INTERVAL_MILLIS,
            )
            sleep_seconds = max(
                polling_millis / 1000.0,
                self.settings.MIN_POLL_SECONDS,
            )

            return events, sleep_seconds

        except HttpError as err:
            if "quotaExceeded" in str(err):
                logger.error("YouTube API Quota Exceeded! ChatBrain must halt or pause.")
                raise err
            logger.error("YouTube API HTTP error reading chat: %s", err)
            return [], self.settings.ERROR_RETRY_SECONDS
        except Exception as err:
            logger.error("Error reading live chat messages: %s", err)
            return [], self.settings.ERROR_RETRY_SECONDS
