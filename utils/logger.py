"""Structured and Secure Logger for ChatBrain.

Ensures proper log formatting, level control, and prevents accidental credential leakage.
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Optional


class SensitiveFilter(logging.Filter):
    """Filter that masks sensitive tokens, client secrets, and credential keys in log messages."""

    # Patterns for bearer tokens, api keys, or sensitive json payloads
    PATTERNS = [
        re.compile(r'(?i)(ya29\.[a-zA-Z0-9_\-]+)'),
        re.compile(r'(?i)(AIza[0-9A-Za-z-_]{35})'),
        re.compile(r'(?i)(client_secret["\']?\s*[:=]\s*["\'])([^"\']+)'),
        re.compile(r'(?i)(refresh_token["\']?\s*[:=]\s*["\'])([^"\']+)'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in self.PATTERNS:
                if "client_secret" in pattern.pattern or "refresh_token" in pattern.pattern:
                    msg = pattern.sub(r"\1***MASKED***", msg)
                else:
                    msg = pattern.sub("***MASKED_TOKEN***", msg)
            record.msg = msg
        return True


def setup_logger(
    name: str = "ChatBrain",
    level: str = "INFO",
    log_file: Optional[str] = "chatbrain.log",
) -> logging.Logger:
    """Configure and return the application logger with console and file handlers."""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sensitive_filter = SensitiveFilter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(sensitive_filter)
            logger.addHandler(file_handler)
        except (OSError, IOError) as err:
            logger.warning("Could not initialize file log at %s: %s", log_file, err)

    return logger


def get_logger(name: str = "ChatBrain") -> logging.Logger:
    """Get an existing logger or create a default one."""
    return logging.getLogger(name)
