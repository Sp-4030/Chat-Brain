"""ChatBrain Legacy Entrypoint and Response Generator.

Maintains backward compatibility with legacy imports while delegating
to the modular LLM prompt builder and Ollama client.
"""

from __future__ import annotations

import re
from typing import Optional

from config.settings import get_settings
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from utils.language_detector import detect_language
from utils.logger import get_logger

logger = get_logger("Brain")
settings = get_settings()

MODEL_NAME = settings.OLLAMA_MODEL
MAX_REPLY_LENGTH = settings.MAX_REPLY_LENGTH

_ollama_client: Optional[OllamaClient] = None
_prompt_builder: Optional[PromptBuilder] = None


def get_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(settings)
    return _ollama_client


def get_builder() -> PromptBuilder:
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder(settings)
    return _prompt_builder


# For backward compatibility with scripts accessing brain.llm
llm = get_client()._llm


def clean_message(message: str) -> str:
    """Clean subscriber message removing bot mention tags."""
    return get_builder().clean_message(message)


def clean_reply(reply: str) -> str:
    """Clean model response removing prefixes and limiting length."""
    return get_builder().clean_reply(reply)


def generate_response(message: str) -> str:
    """Generate friendly, concise desi AI response using local Ollama model."""
    builder = get_builder()
    client = get_client()

    user_message = clean_message(message)
    if not user_message:
        return "Bhai kya puchna hai? ChatBrain ready aahe 😄"

    detected_lang = detect_language(user_message)
    prompt = builder.build_prompt(
        message=user_message,
        language=detected_lang,
    )

    try:
        raw_reply, _ = client.generate(prompt)
        reply = clean_reply(raw_reply)
        if not reply:
            return builder.get_fallback_reply(detected_lang)
        return reply
    except Exception as err:
        logger.error("Error generating response in legacy brain module: %s", err)
        return builder.get_fallback_reply(detected_lang)


if __name__ == "__main__":
    print(f"ChatBrain Engine initialized with model '{MODEL_NAME}'")
    test_msg = "Hello ChatBrain, kaise ho?"
    print(f"Sample Input: {test_msg}")
    print(f"Sample Output: {generate_response(test_msg)}")