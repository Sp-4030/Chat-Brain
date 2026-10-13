"""Bounded Conversation Context Management.

Maintains isolated, recent conversational context per viewer and stream-wide
to enable natural follow-ups without polluting context across viewers.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional


@dataclass
class ConversationTurn:
    """A single interaction turn between a viewer and the bot."""

    user_message: str
    bot_reply: str
    timestamp: float = field(default_factory=time.time)
    language: str = "unknown"


class ConversationContextManager:
    """Manages short-term conversation context with strict bounds."""

    def __init__(
        self,
        max_user_turns: int = 3,
        max_global_turns: int = 5,
        max_tracked_users: int = 200,
    ) -> None:
        self.max_user_turns = max_user_turns
        self.max_global_turns = max_global_turns
        self.max_tracked_users = max_tracked_users
        self._user_contexts: Dict[str, Deque[ConversationTurn]] = {}
        self._global_context: Deque[tuple[str, ConversationTurn]] = deque(maxlen=max_global_turns)

    def add_interaction(
        self,
        user_key: str,
        user_name: str,
        user_message: str,
        bot_reply: str,
        language: str = "unknown",
    ) -> None:
        """Store a completed conversation turn for a user and global history."""
        if not user_key:
            user_key = f"name:{user_name.lower()}"

        if user_key not in self._user_contexts:
            # Enforce max tracked users bound
            if len(self._user_contexts) >= self.max_tracked_users:
                oldest_key = next(iter(self._user_contexts))
                del self._user_contexts[oldest_key]
            self._user_contexts[user_key] = deque(maxlen=self.max_user_turns)

        turn = ConversationTurn(
            user_message=user_message,
            bot_reply=bot_reply,
            language=language,
        )
        self._user_contexts[user_key].append(turn)
        self._global_context.append((user_name, turn))

    def get_user_context(self, user_key: str) -> List[ConversationTurn]:
        """Retrieve recent interaction turns for a specific user."""
        if not user_key or user_key not in self._user_contexts:
            return []
        return list(self._user_contexts[user_key])

    def format_user_context_prompt(self, user_key: str) -> str:
        """Format recent turns into a concise context block for prompt builder."""
        turns = self.get_user_context(user_key)
        if not turns:
            return ""

        lines = ["RECENT CONVERSATION WITH THIS VIEWER:"]
        for idx, turn in enumerate(turns, 1):
            lines.append(f"- Viewer: {turn.user_message}")
            lines.append(f"  ChatBrain: {turn.bot_reply}")
        return "\n".join(lines)

    def clear(self) -> None:
        """Reset all in-memory context."""
        self._user_contexts.clear()
        self._global_context.clear()
