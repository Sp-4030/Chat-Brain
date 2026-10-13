"""Safety and Spam Filters for Live Chat Messages.

Validates message content, filters spam patterns, blocked keywords, and malformed inputs.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from utils.logger import get_logger

logger = get_logger("SafetyRules")


class SafetyRules:
    """Evaluates message safety, spam indicators, and content integrity."""

    def __init__(self, blocked_keywords: List[str] | None = None) -> None:
        self.blocked_keywords = [k.lower() for k in (blocked_keywords or [])]

    def is_safe(self, text: str) -> Tuple[bool, str]:
        """Check whether the message passes safety and anti-spam filters."""
        if not text or not text.strip():
            return False, "Empty message"

        cleaned = text.strip()

        # Maximum incoming length protection
        if len(cleaned) > 500:
            return False, "Message exceeds length limit (500 chars)"

        text_lower = cleaned.lower()

        # Blocked keywords check
        for keyword in self.blocked_keywords:
            if keyword in text_lower:
                return False, f"Contains blocked keyword: '{keyword}'"

        # URL / link spam check
        if re.search(r"https?://|www\.|t\.me/|wa\.me/|bit\.ly/", text_lower):
            return False, "Contains URL or promotional link"

        # Excessive character repetition check (e.g., 'heyyyyyyy' > 6 times is fine, but 15+ is spam)
        if re.search(r"(.)\1{14,}", cleaned):
            return False, "Excessive repeated characters"

        # Excessive emoji or symbol-only check
        non_symbols = re.sub(r"[^\w\s\u0900-\u097F]", "", cleaned)
        if len(cleaned) > 10 and len(non_symbols.strip()) == 0:
            return False, "Message contains only symbols/emojis"

        return True, "Safe"
