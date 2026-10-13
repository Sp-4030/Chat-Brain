"""YouTube Live Chat Integration Entrypoint.

Maintains backwards compatibility with legacy functions while leveraging the
new modular architecture (YouTubeClientManager, LiveChatReader, MessageSender, ChatService).
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, Set

from config.settings import get_settings
from decision.reply_decision import ReplyDecisionEngine
from identity.user_identity import UserIdentityManager
from memory.conversation_memory import ConversationMemory
from services.chat_service import ChatService
from utils.logger import get_logger
from youtube.client import YouTubeClientManager
from youtube.live_chat_reader import LiveChatReader
from youtube.message_sender import YouTubeMessageSender
from brain import generate_response

logger = get_logger("YouTube")
settings = get_settings()

# Legacy configuration attributes preserved for backward compatibility
SCOPES = settings.SCOPES
CLIENT_SECRET_FILE = settings.CLIENT_SECRET_FILE
TOKEN_FILE = settings.TOKEN_FILE
HISTORY_FILE = settings.HISTORY_FILE
MAX_REPLY_LENGTH = settings.MAX_REPLY_LENGTH
MIN_POLL_SECONDS = settings.MIN_POLL_SECONDS
ERROR_RETRY_SECONDS = settings.ERROR_RETRY_SECONDS
SMART_REPLY_FILTER = settings.SMART_REPLY_FILTER
BOT_NAMES = settings.BOT_NAMES
QUESTION_WORDS = settings.QUESTION_WORDS


def get_youtube():
    """Authenticate and build YouTube API service client."""
    manager = YouTubeClientManager(settings)
    return manager.get_service()


def get_live_chat_id(youtube):
    """Find active live broadcast's liveChatId."""
    reader = LiveChatReader(youtube, settings)
    return reader.find_active_live_chat_id()


def should_reply(message: str) -> bool:
    """Evaluate whether an incoming message qualifies for a reply."""
    text = message.strip().lower()
    if not text:
        return False

    # Check direct bot mentions
    for bot_name in BOT_NAMES:
        if bot_name in text:
            return True

    # Check question marks
    if "?" in text:
        return True

    # Check question words
    words = text.split()
    for word in QUESTION_WORDS:
        if word in words:
            return True

    return False


def send_reply(youtube, live_chat_id: str, reply: str) -> Optional[str]:
    """Send text reply to YouTube Live Chat."""
    sender = YouTubeMessageSender(youtube, settings)
    return sender.send_reply(live_chat_id, reply)


def save_message(author: str, message: str, reply: str, posted: bool) -> None:
    """Save interaction to chat_history.jsonl."""
    memory = ConversationMemory(settings.HISTORY_FILE)
    memory.save_interaction(
        author=author,
        message=message,
        reply=reply,
        posted_to_youtube=posted,
    )


def process_message(
    youtube,
    live_chat_id: str,
    item: Dict[str, Any],
    processed_messages: Set[str],
) -> None:
    """Process a single incoming message from YouTube Live Chat."""
    message_id = item.get("id")
    if not message_id or message_id in processed_messages:
        return

    processed_messages.add(message_id)

    author_details = item.get("authorDetails", {})
    author = author_details.get("displayName", "Unknown")

    snippet = item.get("snippet", {})
    message = snippet.get("displayMessage", "").strip()

    if not message:
        return

    print("----------------------------------------")
    print(f"Subscriber: {author}")
    print(f"Message: {message}")

    if SMART_REPLY_FILTER and not should_reply(message):
        print("ChatBrain: Ignored (not a question/request)")
        print("----------------------------------------\n")
        return

    reply = generate_response(message)
    print(f"ChatBrain: {reply}")

    reply_id = send_reply(youtube, live_chat_id, reply)
    posted = reply_id is not None

    save_message(author, message, reply, posted)

    if reply_id:
        processed_messages.add(reply_id)

    print(f"Posted: {posted}")
    print("----------------------------------------\n")


def start_chat(youtube, live_chat_id: str) -> None:
    """Start legacy polling loop."""
    print("\n========================================")
    print("        CHATBRAIN IS CONNECTED")
    print("========================================\n")
    print("YouTube : CONNECTED")
    print("Ollama  : CONNECTED")
    print("Reply   : ENABLED")
    print(f"Filter  : {SMART_REPLY_FILTER}\n")
    print("Waiting for subscriber messages...\n")

    processed_messages: Set[str] = set()
    first_request = True

    while True:
        try:
            response = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails",
            ).execute()

            messages = response.get("items", [])

            if first_request:
                for item in messages:
                    mid = item.get("id")
                    if mid:
                        processed_messages.add(mid)
                first_request = False
                print("Existing messages loaded.")
            else:
                for item in messages:
                    process_message(youtube, live_chat_id, item, processed_messages)

            polling_interval = response.get("pollingIntervalMillis", 5000)
            polling_seconds = max(polling_interval / 1000.0, MIN_POLL_SECONDS)
            time.sleep(polling_seconds)

        except KeyboardInterrupt:
            print("\n========================================")
            print("       CHATBRAIN STOPPED")
            print("========================================\n")
            break

        except Exception as error:
            print(f"\nError in polling loop: {error}")
            time.sleep(ERROR_RETRY_SECONDS)


def main():
    """Application entry point using the new modular ChatService."""
    service = ChatService(settings)
    service.start()


if __name__ == "__main__":
    main()
