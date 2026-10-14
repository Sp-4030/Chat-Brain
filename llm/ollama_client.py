"""Local Ollama Client for ChatBrain.

Provides reliable local inference management, timeout handling, connection health checks,
and controlled retries using Ollama.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import List, Optional, Tuple

from langchain_ollama import ChatOllama
from config.settings import Settings, get_settings
from utils.logger import get_logger

logger = get_logger("OllamaClient")


class OllamaClient:
    """Manages connection and inference requests to the local Ollama instance."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = self.settings.OLLAMA_MODEL
        self.temperature = self.settings.OLLAMA_TEMPERATURE
        self.timeout = self.settings.OLLAMA_TIMEOUT
        self.max_retries = self.settings.OLLAMA_MAX_RETRIES

        # Build extra kwargs only when a token cap is set
        extra_kwargs: dict = {}
        if self.settings.OLLAMA_MAX_TOKENS > 0:
            extra_kwargs["num_predict"] = self.settings.OLLAMA_MAX_TOKENS

        self._llm = ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            temperature=self.temperature,
            timeout=self.timeout,
            **extra_kwargs,
        )

    def check_health(self) -> Tuple[bool, List[str], str]:
        """Check whether local Ollama is reachable and return list of installed models."""
        tags_url = f"{self.base_url}/api/tags"
        req = urllib.request.Request(tags_url, headers={"User-Agent": "ChatBrain/2.0"})

        try:
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    model_found = any(self.model_name in m or m.startswith(self.model_name) for m in models)
                    if not model_found and models:
                        msg = (
                            f"Ollama is running, but model '{self.model_name}' was not found. "
                            f"Installed models: {', '.join(models)}. Run: ollama pull {self.model_name}"
                        )
                        return False, models, msg
                    return True, models, "Ollama is healthy and ready"
                return False, [], f"Ollama returned unexpected HTTP {response.status}"
        except urllib.error.URLError as err:
            msg = (
                f"Could not connect to Ollama at {self.base_url}: {err}. "
                "Ensure Ollama is started locally (run 'ollama serve' or open the Ollama app)."
            )
            return False, [], msg
        except Exception as err:
            return False, [], f"Error checking Ollama status: {err}"

    def generate(self, prompt: str) -> Tuple[str, float]:
        """Send prompt to Ollama with timeout and retry handling.

        Returns:
            Tuple of (response_text, latency_in_seconds).
        """
        start_time = time.time()
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._llm.invoke(prompt)
                latency = time.time() - start_time
                content = getattr(response, "content", "").strip()
                return content, latency
            except Exception as err:
                last_error = err
                logger.warning(
                    "Ollama inference attempt %d/%d failed: %s",
                    attempt,
                    self.max_retries,
                    err,
                )
                if attempt < self.max_retries:
                    time.sleep(1.0)

        latency = time.time() - start_time
        logger.error("All Ollama generation attempts failed: %s", last_error)
        return "", latency
