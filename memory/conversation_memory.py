"""Conversation Memory and History Persistence.

Provides bounded in-memory tracking to prevent duplicate message processing
and duplicate replies, combined with persistent JSONL append logging.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Set
from utils.logger import get_logger

logger = get_logger("ConversationMemory")


class ConversationMemory:
    """Bounded in-memory store and JSONL persistence for live chat interactions."""

    def __init__(self, history_file: str = "chat_history.jsonl", max_cache_size: int = 2000) -> None:
        self.history_file = history_file
        self.max_cache_size = max_cache_size
        self._lock = threading.Lock()

        # Bounded sets for duplicate prevention
        self._processed_ids: Set[str] = set()
        self._processed_order: deque[str] = deque(maxlen=max_cache_size)

        # Recent outgoing replies to avoid repeating exact sentences
        self._recent_replies: deque[str] = deque(maxlen=30)

    def is_processed(self, message_id: str) -> bool:
        """Check if this message ID has already been seen or processed."""
        if not message_id:
            return True
        with self._lock:
            return message_id in self._processed_ids

    def mark_processed(self, message_id: str) -> None:
        """Mark a message ID as processed with bounded eviction."""
        if not message_id:
            return
        with self._lock:
            if message_id not in self._processed_ids:
                if len(self._processed_order) >= self.max_cache_size:
                    oldest = self._processed_order.popleft()
                    self._processed_ids.discard(oldest)
                self._processed_order.append(message_id)
                self._processed_ids.add(message_id)

    def is_duplicate_reply(self, reply_text: str) -> bool:
        """Check if this exact reply text was generated very recently."""
        cleaned = reply_text.strip().lower()
        with self._lock:
            return cleaned in self._recent_replies

    def record_reply_text(self, reply_text: str) -> None:
        """Record an outgoing reply text to prevent immediate repetition."""
        cleaned = reply_text.strip().lower()
        with self._lock:
            self._recent_replies.append(cleaned)

    def save_interaction(
        self,
        author: str,
        message: str,
        reply: str,
        posted_to_youtube: bool,
        author_id: str = "",
        language: str = "unknown",
        decision_reason: str = "",
    ) -> bool:
        """Persist interaction to chat_history.jsonl matching existing schema."""
        record: Dict[str, Any] = {
            "author": author,
            "message": message,
            "reply": reply,
            "posted_to_youtube": posted_to_youtube,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "author_id": author_id,
            "language": language,
            "decision_reason": decision_reason,
        }

        try:
            with self._lock:
                with open(self.history_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except Exception as err:
            logger.error("Failed to persist interaction to %s: %s", self.history_file, err)
            return False

    def load_recent_interactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load the most recent interactions from chat_history.jsonl."""
        if not os.path.exists(self.history_file):
            return []

        interactions: List[Dict[str, Any]] = []
        try:
            with self._lock:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                interactions.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            return interactions[-limit:]
        except Exception as err:
            logger.error("Error reading history from %s: %s", self.history_file, err)
            return []
