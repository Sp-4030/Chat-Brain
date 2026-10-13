"""Contextual Humor Engine for ChatBrain.

Generates culturally nuanced, light desi humor hints without forcing jokes
or repeating identical punchlines.
"""

from __future__ import annotations

import random
import time
from collections import deque
from typing import Deque, List, Optional
from utils.logger import get_logger

logger = get_logger("HumorEngine")


class HumorEngine:
    """Manages light humor guidance and prevents joke repetition."""

    # Curated themes for tasteful desi banter
    HUMOR_THEMES = {
        "job_hunt": [
            "BCA degree vs HR 5 years experience demand",
            "Resume bhejte bhejte inbox full zala",
            "Job hunt chal raha hai, offer letter raste me atak gaya",
        ],
        "coding": [
            "Code run hote hi feature, error aate hi coffee break",
            "Bug fix karne gaya, teen naye bugs welcome karne aa gaye",
            "Python se pakki dosti, bas production deploy ka darr",
        ],
        "kolhapur": [
            "Kolhapuri misal jaisa teekha scene",
            "Kolhapur cha naad khula",
        ],
        "student_life": [
            "Exam ke ek raat pehle syllabus dekh ke dukh",
            "DSA samajte samajte chai thandi ho gayi",
        ],
    }

    def __init__(self, enabled: bool = True, intensity: float = 0.7) -> None:
        self.enabled = enabled
        self.intensity = max(0.0, min(1.0, intensity))
        self._recent_themes: Deque[str] = deque(maxlen=6)
        self._last_humor_time: float = 0.0

    def should_apply_humor(self, message: str, is_technical: bool = False) -> bool:
        """Determine if humor is appropriate for this message."""
        if not self.enabled or self.intensity <= 0.0:
            return False

        # Serious or technical questions get straightforward helpful replies
        if is_technical:
            return False

        msg_lower = message.lower()

        # Explicit joke requests always get humor
        if any(w in msg_lower for w in ["joke", "hasav", "hanso", "funny", "kuch sunao"]):
            return True

        # Casual banter gets humor based on intensity probability
        casual_cues = ["kya haal", "kasa ahes", "kasa aahes", "kya scene", "kaam", "job", "setting"]
        if any(cue in msg_lower for cue in casual_cues):
            return random.random() < self.intensity

        # Otherwise sparingly
        return random.random() < (self.intensity * 0.4)

    def get_humor_guidance(self, message: str, language: str) -> Optional[str]:
        """Provide subtle humor guidance instructions to the prompt builder."""
        msg_lower = message.lower()
        is_joke_request = any(w in msg_lower for w in ["joke", "hasav", "hanso", "funny"])

        # Select a theme not recently used
        available_themes = [k for k in self.HUMOR_THEMES if k not in self._recent_themes]
        if not available_themes:
            available_themes = list(self.HUMOR_THEMES.keys())

        selected_theme = random.choice(available_themes)
        self._recent_themes.append(selected_theme)
        examples = self.HUMOR_THEMES[selected_theme]
        example_hint = random.choice(examples)

        if is_joke_request:
            if "marathi" in language:
                return f"Make a short, 1-line funny Marathi joke about student/coding life (e.g. related to '{example_hint}'). Keep it very brief."
            else:
                return f"Tell a short, 1-line witty desi joke in Hinglish (e.g. related to '{example_hint}'). Keep it punchy and short."

        return f"Add subtle friendly banter or light witty touch (inspired by: {example_hint}) if it fits naturally. Do NOT force a punchline if unnecessary."
