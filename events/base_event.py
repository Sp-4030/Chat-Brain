"""Base Event Definition for ChatBrain."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class BaseEvent:
    """Base class for all internal events in the system."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_type(self) -> str:
        return self.__class__.__name__
