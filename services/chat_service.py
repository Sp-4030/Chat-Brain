"""ChatBrain Orchestration Service.

Initializes all subsystems, wires the event-driven pipeline, performs connection checks,
and runs the main YouTube Live Chat polling loop.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from googleapiclient.errors import HttpError

from comedy.humor_engine import HumorEngine
from config.settings import Settings, get_settings
from context.conversation_context import ConversationContextManager
from decision.reply_decision import ReplyDecisionEngine
from decision.safety_rules import SafetyRules
from events.chat_message_event import ChatMessageEvent
from events.event_bus import EventBus, get_event_bus
from identity.user_identity import UserIdentityManager
from learning.interaction_feedback import InteractionFeedbackTracker
from listeners.chat_message_listener import ChatMessageListener
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from memory.conversation_memory import ConversationMemory
from utils.logger import get_logger, setup_logger
from youtube.client import YouTubeClientManager
from youtube.live_chat_reader import LiveChatReader
from youtube.message_sender import YouTubeMessageSender

logger = get_logger("ChatService")


class ChatService:
    """Core service coordinating YouTube polling, AI inference, and event dispatching."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.running: bool = False
        self._consecutive_errors: int = 0

        # Setup logging
        setup_logger(
            name="ChatBrain",
            level=self.settings.LOG_LEVEL,
            log_file=self.settings.LOG_FILE,
        )

        # 1. State and Memory
        self.memory = ConversationMemory(
            history_file=self.settings.HISTORY_FILE,
            max_cache_size=self.settings.MAX_MEMORY_CACHE_SIZE,
        )
        self.identity_manager = UserIdentityManager()
        self.context_manager = ConversationContextManager(
            max_user_turns=self.settings.MAX_CONTEXT_TURNS,
        )
        self.feedback_tracker = InteractionFeedbackTracker()

        # 2. Logic Engines
        self.safety_rules = SafetyRules(blocked_keywords=self.settings.BLOCKED_KEYWORDS)
        self.decision_engine = ReplyDecisionEngine(
            settings=self.settings,
            identity_manager=self.identity_manager,
            safety_rules=self.safety_rules,
        )
        self.humor_engine = HumorEngine(
            enabled=self.settings.HUMOR_ENABLED,
            intensity=self.settings.HUMOR_INTENSITY,
        )

        # 3. AI / LLM
        self.ollama_client = OllamaClient(settings=self.settings)
        self.prompt_builder = PromptBuilder(settings=self.settings)

        # 4. YouTube Components (deferred initialization until start)
        self.youtube_manager = YouTubeClientManager(settings=self.settings)
        self.reader: Optional[LiveChatReader] = None
        self.sender: Optional[YouTubeMessageSender] = None

        # 5. Events & Listener
        self.event_bus: EventBus = get_event_bus()
        self.listener: Optional[ChatMessageListener] = None

    def initialize_pipeline(self) -> bool:
        """Initialize YouTube API connections and register event listeners."""
        # 1. Check local Ollama health
        ollama_ok, models, ollama_msg = self.ollama_client.check_health()
        if ollama_ok:
            logger.info("Ollama Status: %s", ollama_msg)
        else:
            logger.warning("Ollama Warning: %s", ollama_msg)

        # 2. YouTube OAuth & Service
        try:
            youtube_service = self.youtube_manager.get_service()
            logger.info("YouTube OAuth authentication successful.")
        except Exception as err:
            logger.error("Failed to authenticate YouTube client: %s", err)
            return False

        # Identify authenticated channel to avoid self-replies
        bot_channel_id, bot_name = self.youtube_manager.get_authenticated_channel_info()
        if bot_channel_id:
            logger.info("Bot Channel Identified: %s (%s)", bot_name, bot_channel_id)
            self.identity_manager.set_bot_identity(bot_channel_id, self.settings.BOT_NAMES)

        # 3. Create Reader & Sender
        self.reader = LiveChatReader(youtube_service, self.settings)
        self.sender = YouTubeMessageSender(youtube_service, self.settings)

        # 4. Search for active live stream
        live_chat_id = self.reader.find_active_live_chat_id()
        if not live_chat_id:
            logger.warning("No active YouTube Live broadcast found. Please start your live stream first.")
            return False

        # 5. Wire Listener and subscribe to EventBus
        self.listener = ChatMessageListener(
            settings=self.settings,
            memory=self.memory,
            identity_manager=self.identity_manager,
            decision_engine=self.decision_engine,
            context_manager=self.context_manager,
            humor_engine=self.humor_engine,
            ollama_client=self.ollama_client,
            prompt_builder=self.prompt_builder,
            message_sender=self.sender,
            feedback_tracker=self.feedback_tracker,
            live_chat_id=live_chat_id,
        )

        self.event_bus.subscribe(ChatMessageEvent, self.listener.handle_message)
        logger.info("Event listener registered for ChatMessageEvent.")
        return True

    def start(self) -> None:
        """Start the main live chat monitoring loop."""
        print()
        print("========================================")
        print("          CHATBRAIN STARTING")
        print("========================================")
        print()

        # Validate configuration
        warnings = self.settings.validate()
        for w in warnings:
            logger.warning("Config Warning: %s", w)

        if not self.initialize_pipeline():
            print()
            print("========================================")
            print("       CHATBRAIN STARTUP FAILED")
            print("========================================")
            print("Please ensure client_secret.json is in place and your YouTube stream is live.")
            return

        self.running = True
        print()
        print("========================================")
        print("        CHATBRAIN IS CONNECTED")
        print("========================================")
        print("YouTube : CONNECTED")
        print(f"Ollama  : {self.settings.OLLAMA_MODEL} ({self.settings.OLLAMA_BASE_URL})")
        print(f"Filter  : {'SMART' if self.settings.SMART_REPLY_FILTER else 'ALL'}")
        print()
        print("Waiting for subscriber messages... (Press Ctrl+C to stop)")
        print()

        first_poll = True

        while self.running:
            try:
                events, sleep_seconds = self.reader.fetch_messages()
                self._consecutive_errors = 0

                if first_poll:
                    # On first poll, record existing chat messages so bot doesn't reply to history
                    for event in events:
                        self.memory.mark_processed(event.message_id)
                    first_poll = False
                    logger.info("Loaded %d existing messages from chat history.", len(events))
                else:
                    # Dispatch new events to listener
                    for event in events:
                        self.event_bus.publish(event)

                time.sleep(sleep_seconds)

            except KeyboardInterrupt:
                logger.info("Shutdown requested via KeyboardInterrupt.")
                self.stop()
                break

            except HttpError as err:
                if "quotaExceeded" in str(err):
                    logger.critical("YouTube Daily API Quota is exhausted. Stopping ChatBrain.")
                    self.stop()
                    break

                self._consecutive_errors += 1
                logger.warning(
                    "YouTube API error (Attempt %d/%d): %s",
                    self._consecutive_errors,
                    self.settings.MAX_CONSECUTIVE_ERRORS,
                    err,
                )
                time.sleep(self.settings.ERROR_RETRY_SECONDS)

            except Exception as err:
                self._consecutive_errors += 1
                logger.error("Unexpected error in poll loop: %s", err, exc_info=True)
                time.sleep(self.settings.ERROR_RETRY_SECONDS)

    def stop(self) -> None:
        """Gracefully terminate live chat polling."""
        self.running = False
        print()
        print("========================================")
        print("       CHATBRAIN STOPPED")
        print("========================================")
        print()
        summary = self.feedback_tracker.get_summary()
        logger.info(
            "Session Summary: %d received, %d ignored, %d generated, %d sent.",
            summary.get("messages_received", 0),
            summary.get("messages_ignored", 0),
            summary.get("replies_generated", 0),
            summary.get("replies_sent", 0),
        )

    def get_status(self) -> Dict[str, Any]:
        """Return runtime status snapshot for dashboards."""
        return {
            "running": self.running,
            "live_chat_id": self.reader.live_chat_id if self.reader else None,
            "broadcast_title": self.reader.active_broadcast_title if self.reader else None,
            "telemetry": self.feedback_tracker.get_summary(),
        }
