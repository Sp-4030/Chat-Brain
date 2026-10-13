"""Chat Message Event Listener.

Orchestrates message processing from event reception through decision-making,
AI inference, YouTube response delivery, and persistence.
"""

from __future__ import annotations

from typing import Optional

from comedy.humor_engine import HumorEngine
from config.settings import Settings, get_settings
from context.conversation_context import ConversationContextManager
from decision.reply_decision import ReplyDecisionEngine
from events.chat_message_event import ChatMessageEvent
from identity.user_identity import UserIdentityManager
from learning.interaction_feedback import InteractionFeedbackTracker
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from memory.conversation_memory import ConversationMemory
from utils.language_detector import detect_language
from utils.logger import get_logger
from youtube.message_sender import YouTubeMessageSender

logger = get_logger("ChatMessageListener")


class ChatMessageListener:
    """Processes ChatMessageEvent by coordinating the response generation pipeline."""

    def __init__(
        self,
        settings: Settings,
        memory: ConversationMemory,
        identity_manager: UserIdentityManager,
        decision_engine: ReplyDecisionEngine,
        context_manager: ConversationContextManager,
        humor_engine: HumorEngine,
        ollama_client: OllamaClient,
        prompt_builder: PromptBuilder,
        message_sender: Optional[YouTubeMessageSender] = None,
        feedback_tracker: Optional[InteractionFeedbackTracker] = None,
        live_chat_id: Optional[str] = None,
    ) -> None:
        self.settings = settings
        self.memory = memory
        self.identity_manager = identity_manager
        self.decision_engine = decision_engine
        self.context_manager = context_manager
        self.humor_engine = humor_engine
        self.ollama_client = ollama_client
        self.prompt_builder = prompt_builder
        self.message_sender = message_sender
        self.feedback_tracker = feedback_tracker or InteractionFeedbackTracker()
        self.live_chat_id = live_chat_id

    def set_live_chat_id(self, live_chat_id: str) -> None:
        """Set the active YouTube live chat ID."""
        self.live_chat_id = live_chat_id

    def handle_message(self, event: ChatMessageEvent) -> None:
        """Handle incoming ChatMessageEvent through the processing pipeline."""
        if not event or not event.message_id:
            return

        # 1. Telemetry
        self.feedback_tracker.record_received()

        # 2. Duplicate incoming message filter
        if self.memory.is_processed(event.message_id):
            logger.debug("Message %s already processed. Skipping.", event.message_id)
            return

        self.memory.mark_processed(event.message_id)

        # 3. Log arrival
        logger.info(
            "Incoming message | Author: %s | Text: '%s'",
            event.author_name,
            event.text,
        )

        # 4. Update viewer identity record
        self.identity_manager.get_or_create(
            user_id=event.author_id,
            display_name=event.author_name,
            is_owner=event.is_owner,
            is_moderator=event.is_moderator,
            is_sponsor=event.is_sponsor,
        )

        # 5. Reply Decision Engine
        decision = self.decision_engine.evaluate(
            text=event.text,
            author_id=event.author_id,
            author_name=event.author_name,
        )

        if not decision.should_reply:
            logger.info("Message skipped by decision engine: %s", decision.reason)
            self.feedback_tracker.record_ignored(decision.reason)
            return

        # 6. Language Detection
        detected_language = detect_language(event.text)
        event.detected_language = detected_language
        logger.debug("Detected language for message: %s", detected_language)

        # 7. Context Retrieval
        user_key = event.author_id or f"name:{event.author_name.lower()}"
        context_str = self.context_manager.format_user_context_prompt(user_key)

        # 8. Humor Guidance
        humor_hint = None
        if self.humor_engine.should_apply_humor(event.text):
            humor_hint = self.humor_engine.get_humor_guidance(event.text, detected_language)

        # 9. Prompt Construction
        prompt = self.prompt_builder.build_prompt(
            message=event.text,
            author_name=event.author_name,
            language=detected_language,
            context_str=context_str,
            humor_guidance=humor_hint,
        )

        # 10. Ollama Inference
        raw_reply, latency = self.ollama_client.generate(prompt)

        # 11. Response Cleaning & Sanitization
        reply = self.prompt_builder.clean_reply(raw_reply)

        if not reply:
            logger.warning("Ollama produced empty reply. Using fallback message.")
            reply = self.prompt_builder.get_fallback_reply(detected_language)
            self.feedback_tracker.record_error()
        else:
            self.feedback_tracker.record_reply_generated(latency)

        # 12. Duplicate Outgoing Reply Prevention
        if self.memory.is_duplicate_reply(reply):
            logger.info("Generated reply was identical to a very recent reply. Adding slight variation.")
            reply = f"{reply} 👍"

        self.memory.record_reply_text(reply)

        logger.info("Generated reply (in %.2fs) for %s: '%s'", latency, event.author_name, reply)

        # 13. YouTube Message Dispatch
        posted_to_youtube = False
        reply_id = None

        if self.message_sender and self.live_chat_id:
            reply_id = self.message_sender.send_reply(self.live_chat_id, reply)
            posted_to_youtube = reply_id is not None
            if posted_to_youtube:
                self.feedback_tracker.record_reply_sent()
                self.decision_engine.record_reply_dispatched(event.author_id, event.author_name)
                if reply_id:
                    self.memory.mark_processed(reply_id)
            else:
                self.feedback_tracker.record_reply_skipped("Send failed or quota exceeded")
        else:
            logger.info("Message sender or live_chat_id inactive. Simulating local dispatch.")
            self.decision_engine.record_reply_dispatched(event.author_id, event.author_name)

        # 14. Conversation Context Update
        self.context_manager.add_interaction(
            user_key=user_key,
            user_name=event.author_name,
            user_message=event.text,
            bot_reply=reply,
            language=detected_language,
        )

        # 15. History Persistence
        self.memory.save_interaction(
            author=event.author_name,
            message=event.text,
            reply=reply,
            posted_to_youtube=posted_to_youtube,
            author_id=event.author_id,
            language=detected_language,
            decision_reason=decision.reason,
        )
