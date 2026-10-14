"""Intent Detector for ChatBrain.

Classifies each incoming viewer message into one of four intents so the
prompt builder can choose the correct persona block:

  - "shantanu_roast"  : viewer is asking about Shantanu's job/career/life
  - "chatbrain_self"  : viewer is explicitly talking TO or ABOUT ChatBrain
  - "topic_query"     : factual / topic question (anime, tech, etc.)
  - "general"         : casual chat, greetings, reactions

Classification uses keyword matching so it works completely offline and adds
zero latency.  It is intentionally conservative: only "shantanu_roast" and
"chatbrain_self" are forced; everything else falls through to the LLM with
appropriately-flavoured prompt guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from utils.logger import get_logger

logger = get_logger("IntentDetector")

# ---------------------------------------------------------------------------
# Intent labels (importable constants)
# ---------------------------------------------------------------------------
INTENT_SHANTANU_ROAST = "shantanu_roast"
INTENT_CHATBRAIN_SELF = "chatbrain_self"
INTENT_TOPIC_QUERY = "topic_query"
INTENT_GENERAL = "general"


@dataclass
class IntentResult:
    """The detected intent for a viewer message."""

    intent: str
    confidence: str      # "high" | "medium" | "low"
    matched_signal: str  # human-readable explanation for logging


class IntentDetector:
    """Offline, keyword-based viewer message intent classifier."""

    # -----------------------------------------------------------------------
    # Signal word sets — keep them short and easy to extend
    # -----------------------------------------------------------------------

    # Job / career / personal-status words that point at Shantanu
    _SHANTANU_JOB_SIGNALS: List[str] = [
        # Hinglish / Hindi
        "kaam", "kya karta", "kya karte", "kya kar raha", "kya karega",
        "job", "naukri", "nokri",
        "career", "karier",
        "salary", "paisa", "income", "kamaai", "kamai",
        "berojgar", "unemployed",
        "successful", "success", "safal",
        # English
        "what do you do", "what does he do", "what does shantanu do",
        "what is his job", "what is shantanu's job",
        "does he work", "does shantanu work",
        "is he employed", "is shantanu employed",
        "what is he doing",
    ]

    # Explicit references to Shantanu by name / pronoun
    _SHANTANU_NAME_SIGNALS: List[str] = [
        "shantanu",
    ]

    # Ambiguous first / second-person pronouns used in livestream context —
    # treated as "about Shantanu" ONLY when paired with a job signal
    _AMBIGUOUS_PRONOUNS: List[str] = [
        "aap", "tum", "tu", "you", "he", "vo", "voh", "woh", "wo",
    ]

    # Words that point at the BOT itself
    _CHATBRAIN_SIGNALS: List[str] = [
        "chatbrain", "chat brain", "chat-brain",
        "@chatbrain", "@chat-brain",
    ]

    # Light topic / content signals
    _TOPIC_SIGNALS: List[str] = [
        "anime", "manga", "series", "movie", "film", "game",
        "recommend", "suggestion", "suggest",
        "python", "code", "coding", "programming", "linux", "ai",
        "error", "bug", "kya hai", "what is", "explain",
        "dark anime", "horror", "thriller",
    ]

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def detect(self, message: str, author_name: str = "") -> IntentResult:
        """Return the classified intent for *message*.

        Parameters
        ----------
        message:
            Raw viewer message text.
        author_name:
            Viewer display name (reserved for future per-user context).
        """
        if not message:
            return IntentResult(INTENT_GENERAL, "low", "empty message")

        text = message.strip().lower()

        # 1. Explicit ChatBrain mention → always chatbrain_self
        if self._matches_any(text, self._CHATBRAIN_SIGNALS):
            # Only escalate to roast when the Shantanu name is also present
            # e.g. "chatbrain, shantanu kya karta hai?" → roast
            # but "chatbrain tu kya karta hai?" → chatbrain_self
            if (
                self._matches_any(text, self._SHANTANU_NAME_SIGNALS)
                and self._matches_any(text, self._SHANTANU_JOB_SIGNALS)
            ):
                return IntentResult(
                    INTENT_SHANTANU_ROAST,
                    "high",
                    "chatbrain mention + shantanu name + job signal",
                )
            return IntentResult(
                INTENT_CHATBRAIN_SELF,
                "high",
                "explicit chatbrain mention",
            )

        has_job_signal = self._matches_any(text, self._SHANTANU_JOB_SIGNALS)
        has_shantanu_name = self._matches_any(text, self._SHANTANU_NAME_SIGNALS)

        # 2. Shantanu name + job signal → roast (high confidence)
        if has_shantanu_name and has_job_signal:
            return IntentResult(
                INTENT_SHANTANU_ROAST,
                "high",
                "shantanu name + job signal",
            )

        # 3. Shantanu name alone in a short message → roast (medium)
        if has_shantanu_name:
            if len(text.split()) <= 8:
                return IntentResult(
                    INTENT_SHANTANU_ROAST,
                    "medium",
                    "shantanu name in short message",
                )

        # 4. Ambiguous pronoun + job signal → inferred as streamer question
        has_pronoun = self._matches_any(text, self._AMBIGUOUS_PRONOUNS)
        if has_pronoun and has_job_signal:
            return IntentResult(
                INTENT_SHANTANU_ROAST,
                "medium",
                "pronoun + job signal → streamer question inferred",
            )

        # 5. Pure job signal (e.g. "kya kaam karte ho?") → roast
        if has_job_signal:
            return IntentResult(
                INTENT_SHANTANU_ROAST,
                "medium",
                "job signal only → streamer question inferred",
            )

        # 6. Topic / content question
        if self._matches_any(text, self._TOPIC_SIGNALS):
            return IntentResult(
                INTENT_TOPIC_QUERY,
                "medium",
                "topic/content signal detected",
            )

        # 7. Fallthrough → general casual chat
        return IntentResult(INTENT_GENERAL, "low", "no strong signal")

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _matches_any(text: str, signals: List[str]) -> bool:
        """Return True if *text* contains any of the given signal strings."""
        for signal in signals:
            if signal in text:
                return True
        return False
