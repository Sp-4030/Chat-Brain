"""Viewer Identity and Cooldown Tracking.

Tracks active viewers using stable identifiers, manages per-user rate limits,
and prevents responding to the chatbot itself.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("UserIdentity")


@dataclass
class UserProfile:
    """Represents a unique viewer in the live stream."""

    user_id: str
    display_name: str
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    message_count: int = 0
    reply_count: int = 0
    last_reply_time: float = 0.0
    reply_timestamps: List[float] = field(default_factory=list)
    is_owner: bool = False
    is_moderator: bool = False
    is_sponsor: bool = False


class UserIdentityManager:
    """Manages viewer identities and enforces per-user cooldowns."""

    def __init__(self, max_users: int = 1000) -> None:
        self.max_users = max_users
        self._users: OrderedDict[str, UserProfile] = OrderedDict()
        self.bot_channel_id: Optional[str] = None
        self.bot_display_names: List[str] = ["chatbrain", "@chatbrain", "chat-brain"]

    def set_bot_identity(self, channel_id: Optional[str], names: Optional[List[str]] = None) -> None:
        """Register the bot's own channel ID and display names for self-detection."""
        if channel_id:
            self.bot_channel_id = channel_id
        if names:
            self.bot_display_names = [n.lower() for n in names]

    def is_bot_self(self, user_id: str, display_name: str) -> bool:
        """Check if the given author represents the bot itself."""
        if self.bot_channel_id and user_id and user_id == self.bot_channel_id:
            return True
        name_clean = display_name.strip().lower()
        if any(name_clean == b.lower() for b in self.bot_display_names):
            return True
        return False

    def get_or_create(
        self,
        user_id: str,
        display_name: str,
        is_owner: bool = False,
        is_moderator: bool = False,
        is_sponsor: bool = False,
    ) -> UserProfile:
        """Retrieve existing user profile or create a new bounded entry."""
        key = user_id if user_id else f"name:{display_name.lower()}"

        if key in self._users:
            profile = self._users[key]
            profile.display_name = display_name
            profile.last_seen = time.time()
            profile.message_count += 1
            if is_owner:
                profile.is_owner = True
            if is_moderator:
                profile.is_moderator = True
            if is_sponsor:
                profile.is_sponsor = True
            # Move to end for LRU behavior
            self._users.move_to_end(key)
            return profile

        # Evict oldest if capacity exceeded
        if len(self._users) >= self.max_users:
            self._users.popitem(last=False)

        profile = UserProfile(
            user_id=user_id,
            display_name=display_name,
            message_count=1,
            is_owner=is_owner,
            is_moderator=is_moderator,
            is_sponsor=is_sponsor,
        )
        self._users[key] = profile
        return profile

    def can_reply_to_user(
        self,
        user_id: str,
        display_name: str,
        cooldown_seconds: float = 10.0,
        max_in_window: int = 3,
        window_seconds: float = 60.0,
    ) -> tuple[bool, str]:
        """Check if the bot can reply to this user without violating cooldown rules."""
        if self.is_bot_self(user_id, display_name):
            return False, "Self message from bot"

        key = user_id if user_id else f"name:{display_name.lower()}"
        profile = self._users.get(key)
        if not profile:
            return True, "New user"

        now = time.time()

        # Cooldown check
        elapsed = now - profile.last_reply_time
        if elapsed < cooldown_seconds:
            return False, f"User cooldown active ({elapsed:.1f}s < {cooldown_seconds}s)"

        # Sliding window check
        recent_replies = [t for t in profile.reply_timestamps if now - t <= window_seconds]
        profile.reply_timestamps = recent_replies
        if len(recent_replies) >= max_in_window:
            return False, f"User exceeded {max_in_window} replies in {window_seconds}s"

        return True, "Eligible"

    def record_reply_sent(self, user_id: str, display_name: str) -> None:
        """Update metrics after successfully sending a reply to this user."""
        key = user_id if user_id else f"name:{display_name.lower()}"
        profile = self._users.get(key)
        now = time.time()
        if profile:
            profile.last_reply_time = now
            profile.reply_count += 1
            profile.reply_timestamps.append(now)
