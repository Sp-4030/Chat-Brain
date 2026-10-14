"""Prompt Builder and Response Cleaner for ChatBrain.

Constructs intent-aware persona prompts with multi-language awareness,
context injection, and rigorous output sanitisation.

Intent routing:
  shantanu_roast  → playful roast persona about Shantanu
  chatbrain_self  → direct answer about what ChatBrain is
  topic_query     → factual / content question answer
  general         → casual desi-friend banter
"""

from __future__ import annotations

import random
import re
from typing import List, Optional

from config.settings import Settings, get_settings
from utils.logger import get_logger

logger = get_logger("PromptBuilder")

# Intent labels — kept in sync with decision.intent_detector
INTENT_SHANTANU_ROAST = "shantanu_roast"
INTENT_CHATBRAIN_SELF = "chatbrain_self"
INTENT_TOPIC_QUERY = "topic_query"
INTENT_GENERAL = "general"


class PromptBuilder:
    """Builds persona prompts and post-processes model responses."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        # Track recently used roast lines to avoid repetition
        self._recent_roast_lines: List[str] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def clean_message(self, message: str) -> str:
        """Strip bot mentions and normalise whitespace."""
        if not message:
            return ""
        cleaned = re.sub(r"@?chat-?brain\b", "", message, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def pick_roast_line(self) -> str:
        """Pick a roast line that was not used recently, substituting the streamer name."""
        lines = self.settings.ROAST_LINES
        if not lines:
            return f"{self.settings.STREAMER_NAME} berojgar hai bhai 😂"

        # Avoid repeating the last two lines where possible
        available = [l for l in lines if l not in self._recent_roast_lines]
        if not available:
            available = lines
            self._recent_roast_lines.clear()

        chosen = random.choice(available)
        self._recent_roast_lines.append(chosen)
        # Keep the recency window bounded
        if len(self._recent_roast_lines) > min(3, len(lines)):
            self._recent_roast_lines.pop(0)

        return chosen.replace("{name}", self.settings.STREAMER_NAME)

    def build_prompt(
        self,
        message: str,
        author_name: str = "Subscriber",
        language: str = "unknown",
        context_str: str = "",
        humor_guidance: Optional[str] = None,
        intent: str = INTENT_GENERAL,
    ) -> str:
        """Construct full inference prompt with intent-aware persona and guardrails."""
        user_message = self.clean_message(message)

        lang_instruction = self._get_language_instruction(language)
        context_block = f"\n{context_str}\n" if context_str else ""

        # Build the intent-specific persona section
        persona_block = self._build_persona_block(intent, humor_guidance)

        prompt = f"""{persona_block}
{lang_instruction}

{context_block}
CURRENT VIEWER: {author_name}
VIEWER MESSAGE: {user_message}

RESPONSE RULES:
- Exactly 1 short sentence, 3-15 words maximum.
- Match viewer's language and vibe exactly.
- Do NOT repeat the viewer's question.
- Do NOT start with "ChatBrain:" or "Reply:" or "As an AI".
- Do NOT explain yourself or add disclaimers.
- Do NOT write more than one sentence.

REPLY:"""
        return prompt.strip()

    # ------------------------------------------------------------------
    # Persona blocks per intent
    # ------------------------------------------------------------------

    def _build_persona_block(self, intent: str, humor_guidance: Optional[str]) -> str:
        """Return the appropriate system persona block for the given intent."""
        name = self.settings.STREAMER_NAME

        if intent == INTENT_SHANTANU_ROAST and self.settings.ROAST_ENABLED:
            roast_examples = "\n".join(
                f"  - \"{r.replace('{name}', name)}\""
                for r in self.settings.ROAST_LINES[:4]
            )
            return f"""You are ChatBrain, a funny desi YouTube Live Chat bot in {name}'s stream.

SITUATION: A viewer is asking about {name}'s job, career, or what he does.
TASK: Reply with ONE short, playful, friendly joke about {name}'s career situation.

ROAST STYLE EXAMPLES (use the spirit, NOT the exact wording every time):
{roast_examples}

RULES FOR THIS REPLY:
- ONE sentence, max 12 words.
- Use a different wording/phrasing than the examples — vary it.
- Keep it friendly and lighthearted. Never mean or hateful.
- Use natural Hinglish/Hindi/English as the viewer used.
- Do NOT say you are an AI. Do NOT introduce yourself.
- Do NOT make up other personal facts about {name} beyond the career joke."""

        if intent == INTENT_CHATBRAIN_SELF:
            return f"""You are ChatBrain, a witty desi YouTube Live Chat bot in {name}'s stream.

SITUATION: A viewer is directly asking ChatBrain what it is or what it does.
TASK: Give a short, casual, friendly reply about what ChatBrain does in the stream.

EXAMPLES:
  - "Main {name} ki taraf se chat sambhalta hoon bhai 😄"
  - "Main yahan stream mein baat karne ke liye hoon 😄"
  - "I'm the stream's AI buddy — here to chat with you all!"

RULES:
- ONE sentence, max 12 words.
- Sound casual and friendly, not robotic.
- Do NOT give a long introduction or explain AI concepts."""

        if intent == INTENT_TOPIC_QUERY:
            humor_block = f"\nHUMOR HINT: {humor_guidance}" if humor_guidance else ""
            return f"""You are ChatBrain, a helpful and witty desi YouTube Live Chat bot in {name}'s stream.

SITUATION: A viewer has asked a content/topic question (anime, tech, code, etc.).
TASK: Answer the question directly and concisely.{humor_block}

RULES:
- ONE to TWO short sentences max.
- Be helpful and accurate.
- Sound like a knowledgeable friend, not a textbook.
- Match the viewer's language (Hindi/Hinglish/English/Marathi)."""

        # Default: INTENT_GENERAL — casual desi banter
        humor_block = f"\nHUMOR HINT: {humor_guidance}" if humor_guidance else ""
        return f"""You are ChatBrain, a funny, casual desi friend in {name}'s YouTube Live stream.

SITUATION: Casual chat or general message from a viewer.
TASK: Respond naturally like a friendly Indian friend.{humor_block}

RULES:
- ONE sentence, 3-12 words.
- Sound human and natural. No corporate tone.
- Use casual Hinglish/Hindi/Marathi/English matching the viewer.
- Occasional emojis are fine — don't force them every reply.
- Do NOT start with "Arre bhai" every single time.
- Do NOT say "Main aapko batata hoon" or any formal intro."""

    # ------------------------------------------------------------------
    # Language instruction helper
    # ------------------------------------------------------------------

    def _get_language_instruction(self, language: str) -> str:
        """Return targeted language guidance based on detected language."""
        if language == "marathi_devanagari":
            return (
                "LANGUAGE: Reply in natural Marathi using Devanagari script. Keep it short."
            )
        elif language == "marathi_roman":
            return (
                "LANGUAGE: Reply in Roman Marathi / colloquial Marathi style. Keep it short."
            )
        elif language == "hindi_devanagari":
            return (
                "LANGUAGE: Reply in friendly Hindi using Devanagari script. Keep it short."
            )
        elif language == "hinglish":
            return (
                "LANGUAGE: Reply in natural, conversational Hinglish. Keep it short."
            )
        elif language == "english":
            return (
                "LANGUAGE: Reply in casual, friendly English. Keep it short."
            )
        else:
            return (
                "LANGUAGE: Detect and reply in the SAME language/script as the viewer. "
                "If mixed, use natural Hinglish. Keep it short."
            )

    # ------------------------------------------------------------------
    # Response post-processing
    # ------------------------------------------------------------------

    def clean_reply(self, reply: str) -> str:
        """Strip prefixes, deduplicate sentences, and enforce max length."""
        if not reply:
            return ""

        reply = reply.strip()

        # Remove surrounding quotes
        if (reply.startswith('"') and reply.endswith('"')) or (
            reply.startswith("'") and reply.endswith("'")
        ):
            reply = reply[1:-1].strip()

        # Remove common model prefix tags
        prefixes = [
            "chatbrain:", "chat brain:", "assistant:", "bot:", "reply:",
            "response:", "answer:", "ai:",
        ]
        for prefix in prefixes:
            if reply.lower().startswith(prefix):
                reply = reply[len(prefix):].strip()

        # Remove "As an AI" type openings that sneak through
        ai_openers = re.compile(
            r"^(as an ai|as a language model|i am an ai|i'm an ai)[,\s]+",
            re.IGNORECASE,
        )
        reply = ai_openers.sub("", reply).strip()

        # Deduplicate sentences
        sentences = re.split(r"(?<=[.!?।])\s+", reply)
        cleaned_sentences: list[str] = []
        seen: set[str] = set()
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            key = sentence.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned_sentences.append(sentence)

        reply = " ".join(cleaned_sentences)
        reply = re.sub(r"\s+", " ", reply).strip()

        # Enforce maximum reply length
        max_len = self.settings.MAX_REPLY_LENGTH
        if len(reply) > max_len:
            shortened = reply[: max_len - 3]
            if " " in shortened:
                shortened = shortened.rsplit(" ", 1)[0]
            reply = shortened + "..."

        return reply.strip()

    def get_fallback_reply(self, language: str = "unknown") -> str:
        """Return a pleasant fallback reply if generation fails."""
        if "marathi" in language:
            return "भाऊ थोडा टेक्निकल सीन झाला, परत विचार ना! 😂"
        elif "english" in language:
            return "Had a tiny glitch, ask again in a sec! 😄"
        else:
            return "Bhai thoda technical scene zala, ek baar wapas pucho! 😂"
