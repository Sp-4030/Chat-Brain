"""Operational Interaction Metrics and Feedback Tracker.

Tracks pipeline metrics (messages received, filtered, generated, sent, failed)
for operational observability without attempting model weight modifications.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict


class InteractionFeedbackTracker:
    """Thread-safe operational telemetry for chatbot performance monitoring."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.start_time: float = time.time()
        self.messages_received: int = 0
        self.messages_ignored: int = 0
        self.replies_generated: int = 0
        self.replies_sent: int = 0
        self.replies_skipped: int = 0
        self.processing_errors: int = 0
        self.total_generation_time: float = 0.0

    def record_received(self) -> None:
        with self._lock:
            self.messages_received += 1

    def record_ignored(self, reason: str = "") -> None:
        with self._lock:
            self.messages_ignored += 1

    def record_reply_generated(self, latency_seconds: float) -> None:
        with self._lock:
            self.replies_generated += 1
            self.total_generation_time += latency_seconds

    def record_reply_sent(self) -> None:
        with self._lock:
            self.replies_sent += 1

    def record_reply_skipped(self, reason: str = "") -> None:
        with self._lock:
            self.replies_skipped += 1

    def record_error(self) -> None:
        with self._lock:
            self.processing_errors += 1

    def get_summary(self) -> Dict[str, Any]:
        """Return operational statistics snapshot."""
        with self._lock:
            uptime = max(1.0, time.time() - self.start_time)
            avg_latency = (
                self.total_generation_time / self.replies_generated
                if self.replies_generated > 0
                else 0.0
            )
            return {
                "uptime_seconds": round(uptime, 1),
                "messages_received": self.messages_received,
                "messages_ignored": self.messages_ignored,
                "replies_generated": self.replies_generated,
                "replies_sent": self.replies_sent,
                "replies_skipped": self.replies_skipped,
                "processing_errors": self.processing_errors,
                "avg_generation_latency_sec": round(avg_latency, 2),
            }
