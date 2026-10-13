"""Centralized Configuration for ChatBrain.

Loads environment variables from .env if present and provides typed,
validated application settings with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load .env file from project root if available
load_dotenv(override=False)


@dataclass
class Settings:
    """Application configuration container."""

    # Project Information
    PROJECT_NAME: str = "ChatBrain"
    VERSION: str = "2.0.0"

    # Paths
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    CLIENT_SECRET_FILE: str = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")
    TOKEN_FILE: str = os.getenv("TOKEN_FILE", "token.json")
    HISTORY_FILE: str = os.getenv("HISTORY_FILE", "chat_history.jsonl")
    LOG_FILE: str = os.getenv("LOG_FILE", "chatbrain.log")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Ollama Local AI Settings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.8"))
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "30.0"))
    OLLAMA_MAX_RETRIES: int = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))

    # YouTube API Settings
    SCOPES: List[str] = field(
        default_factory=lambda: ["https://www.googleapis.com/auth/youtube.force-ssl"]
    )
    MIN_POLL_SECONDS: float = float(os.getenv("MIN_POLL_SECONDS", "1.0"))
    DEFAULT_POLL_INTERVAL_MILLIS: int = int(os.getenv("DEFAULT_POLL_INTERVAL_MILLIS", "5000"))
    ERROR_RETRY_SECONDS: float = float(os.getenv("ERROR_RETRY_SECONDS", "10.0"))
    MAX_CONSECUTIVE_ERRORS: int = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "5"))

    # Chat & Reply Controls
    MAX_REPLY_LENGTH: int = int(os.getenv("MAX_REPLY_LENGTH", "200"))
    SMART_REPLY_FILTER: bool = os.getenv("SMART_REPLY_FILTER", "true").lower() in ("1", "true", "yes")
    GLOBAL_REPLY_COOLDOWN_SECONDS: float = float(os.getenv("GLOBAL_REPLY_COOLDOWN_SECONDS", "3.0"))
    USER_REPLY_COOLDOWN_SECONDS: float = float(os.getenv("USER_REPLY_COOLDOWN_SECONDS", "10.0"))
    MAX_REPLIES_PER_USER_WINDOW: int = int(os.getenv("MAX_REPLIES_PER_USER_WINDOW", "3"))
    USER_WINDOW_SECONDS: float = float(os.getenv("USER_WINDOW_SECONDS", "60.0"))
    MAX_CONTEXT_TURNS: int = int(os.getenv("MAX_CONTEXT_TURNS", "5"))
    MAX_MEMORY_CACHE_SIZE: int = int(os.getenv("MAX_MEMORY_CACHE_SIZE", "2000"))

    # Humor Settings
    HUMOR_ENABLED: bool = os.getenv("HUMOR_ENABLED", "true").lower() in ("1", "true", "yes")
    HUMOR_INTENSITY: float = float(os.getenv("HUMOR_INTENSITY", "0.7"))

    # Bot Identifiers
    BOT_NAMES: List[str] = field(
        default_factory=lambda: [
            "chatbrain",
            "@chatbrain",
            "chat-brain",
            "@chat-brain",
        ]
    )

    # Question Detection Words
    QUESTION_WORDS: List[str] = field(
        default_factory=lambda: [
            # English
            "what", "why", "how", "who", "when", "where", "which",
            "can", "could", "should", "is", "are", "do", "does", "will", "would",
            # Hindi / Hinglish
            "kya", "kaise", "kyu", "kyun", "kon", "kaun", "kab", "kaha", "kahan", "hai", "he",
            "batao", "bata", "karega", "hoga", "sach",
            # Marathi / Roman Marathi
            "kay", "kas", "kasa", "kashi", "ka", "kuthe", "kadhi", "kon", "kaay",
            "sang", "sanga", "aahe", "ahes", "kaay"
        ]
    )

    # Blocked Words / Content Safety
    BLOCKED_KEYWORDS: List[str] = field(
        default_factory=lambda: [
            "free robux", "hack", "crypto scam", "telegram link",
            "t.me/", "bit.ly/", "wa.me/"
        ]
    )

    # Streamer Profile Details
    STREAMER_NAME: str = os.getenv("STREAMER_NAME", "Shantanu")
    STREAMER_LOCATION: str = os.getenv("STREAMER_LOCATION", "Kolhapur, Maharashtra, India")
    STREAMER_EDUCATION: str = os.getenv("STREAMER_EDUCATION", "BCA completed")
    STREAMER_INTERESTS: str = os.getenv(
        "STREAMER_INTERESTS",
        "AI/ML, Python, DSA, Data Science, technology, and building AI projects"
    )

    def validate(self) -> List[str]:
        """Validate critical configuration and return list of warnings/issues."""
        issues: List[str] = []
        secret_path = Path(self.CLIENT_SECRET_FILE)
        if not secret_path.is_absolute():
            secret_path = self.BASE_DIR / secret_path

        if not secret_path.exists():
            issues.append(
                f"OAuth client file not found at '{self.CLIENT_SECRET_FILE}'. "
                "YouTube authentication will require this file."
            )

        if self.MAX_REPLY_LENGTH <= 0 or self.MAX_REPLY_LENGTH > 500:
            issues.append(f"MAX_REPLY_LENGTH ({self.MAX_REPLY_LENGTH}) should be between 1 and 500.")

        if self.HUMOR_INTENSITY < 0.0 or self.HUMOR_INTENSITY > 1.0:
            issues.append(f"HUMOR_INTENSITY ({self.HUMOR_INTENSITY}) should be between 0.0 and 1.0.")

        return issues

    def to_safe_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary safe for logging and dashboard display."""
        return {
            "PROJECT_NAME": self.PROJECT_NAME,
            "VERSION": self.VERSION,
            "OLLAMA_MODEL": self.OLLAMA_MODEL,
            "OLLAMA_BASE_URL": self.OLLAMA_BASE_URL,
            "OLLAMA_TEMPERATURE": self.OLLAMA_TEMPERATURE,
            "OLLAMA_TIMEOUT": self.OLLAMA_TIMEOUT,
            "CLIENT_SECRET_FILE": self.CLIENT_SECRET_FILE,
            "TOKEN_FILE": self.TOKEN_FILE,
            "HISTORY_FILE": self.HISTORY_FILE,
            "MAX_REPLY_LENGTH": self.MAX_REPLY_LENGTH,
            "SMART_REPLY_FILTER": self.SMART_REPLY_FILTER,
            "GLOBAL_REPLY_COOLDOWN_SECONDS": self.GLOBAL_REPLY_COOLDOWN_SECONDS,
            "USER_REPLY_COOLDOWN_SECONDS": self.USER_REPLY_COOLDOWN_SECONDS,
            "MAX_CONTEXT_TURNS": self.MAX_CONTEXT_TURNS,
            "HUMOR_ENABLED": self.HUMOR_ENABLED,
            "HUMOR_INTENSITY": self.HUMOR_INTENSITY,
            "STREAMER_NAME": self.STREAMER_NAME,
            "STREAMER_LOCATION": self.STREAMER_LOCATION,
        }


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Singleton getter for application settings."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
