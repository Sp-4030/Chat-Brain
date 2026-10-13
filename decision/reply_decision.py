"""Reply Decision Engine for ChatBrain.

Determines whether an incoming message should receive a bot reply,
balancing viewer engagement, rate limits, and YouTube API quota preservation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from config.settings import Settings
from decision.safety_rules import SafetyRules
from identity.user_identity import UserIdentityManager
from utils.logger import get_logger

logger = get_logger("ReplyDecision")


@dataclass
class DecisionResult:
    """The outcome of evaluating an incoming message."""

    should_reply: bool
    reason: str
    is_direct_mention: bool = False
    is_question: bool = False


class ReplyDecisionEngine:
    """Evaluates incoming live chat messages against conversational heuristics and rate limits."""

    def __init__(
        self,
        settings: Settings,
        identity_manager: UserIdentityManager,
        safety_rules: Optional[SafetyRules] = None,
    ) -> None:
        self.settings = settings
        self.identity_manager = identity_manager
        self.safety_rules = safety_rules or SafetyRules(settings.BLOCKED_KEYWORDS)
        self.last_global_reply_time: float = 0.0

    def evaluate(
        self,
        text: str,
        author_id: str,
        author_name: str,
    ) -> DecisionResult:
        """Decide whether to reply to an incoming message."""
        # 1. Bot Self Check
        if self.identity_manager.is_bot_self(author_id, author_name):
            return DecisionResult(should_reply=False, reason="Ignored: Bot self message")

        # 2. Safety & Spam Check
        safe, safety_reason = self.safety_rules.is_safe(text)
        if not safe:
            return DecisionResult(should_reply=False, reason=f"Ignored: {safety_reason}")

        cleaned_text = text.strip()
        text_lower = cleaned_text.lower()

        # 3. Direct Bot Mention Check
        is_direct_mention = any(bot_name.lower() in text_lower for bot_name in self.settings.BOT_NAMES)

        # 4. Question Detection
        has_question_mark = "?" in text_lower
        words = text_lower.split()
        has_question_word = any(qw in words for qw in self.settings.QUESTION_WORDS)
        is_question = has_question_mark or has_question_word

        # 5. Smart Filter Check (if enabled)
        if self.settings.SMART_REPLY_FILTER and not is_direct_mention and not is_question:
            return DecisionResult(
                should_reply=False,
                reason="Ignored: Not a question or bot mention (Smart Reply Filter active)",
                is_direct_mention=False,
                is_question=False,
            )

        now = time.time()

        # 6. Global Cooldown Check (Skip cooldown check for direct mentions if needed, or enforce minimum interval)
        elapsed_global = now - self.last_global_reply_time
        if elapsed_global < self.settings.GLOBAL_REPLY_COOLDOWN_SECONDS:
            return DecisionResult(
                should_reply=False,
                reason=f"Ignored: Global cooldown active ({elapsed_global:.1f}s < {self.settings.GLOBAL_REPLY_COOLDOWN_SECONDS}s)",
                is_direct_mention=is_direct_mention,
                is_question=is_question,
            )

        # 7. Per-User Cooldown Check
        can_user, user_reason = self.identity_manager.can_reply_to_user(
            user_id=author_id,
            display_name=author_name,
            cooldown_seconds=self.settings.USER_REPLY_COOLDOWN_SECONDS,
            max_in_window=self.settings.MAX_REPLIES_PER_USER_WINDOW,
            window_seconds=self.settings.USER_WINDOW_SECONDS,
        )
        if not can_user and not is_direct_mention:
            return DecisionResult(
                should_reply=False,
                reason=f"Ignored: {user_reason}",
                is_direct_mention=is_direct_mention,
                is_question=is_question,
            )

        # Decision Approved
        reason = "Direct bot mention" if is_direct_mention else ("Question detected" if is_question else "Conversational message")
        return DecisionResult(
            should_reply=True,
            reason=reason,
            is_direct_mention=is_direct_mention,
            is_question=is_question,
        )

    def record_reply_dispatched(self, author_id: str, author_name: str) -> None:
        """Update timestamps after a reply is approved and dispatched."""
        self.last_global_reply_time = time.time()
        self.identity_manager.record_reply_sent(author_id, author_name)
