"""ChatBrain Application Entry Point.

Unified launcher for ChatBrain local AI YouTube live chat assistant.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure root path is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from config.settings import get_settings
from llm.ollama_client import OllamaClient
from services.chat_service import ChatService
from utils.logger import setup_logger


def print_banner(settings) -> None:
    print(r"""
   ____ _           _   ____            _       
  / ___| |__   __ _| |_| __ ) _ __ __ _(_)_ __  
 | |   | '_ \ / _` | __|  _ \| '__/ _` | | '_ \ 
 | |___| | | | (_| | |_| |_) | | | (_| | | | | |
  \____|_| |_|\__,_|\__|____/|_|  \__,_|_|_| |_|
    """)
    print(f" {settings.PROJECT_NAME} v{settings.VERSION} — Local AI YouTube Live Chat Assistant")
    print(f" Model Engine: Ollama ({settings.OLLAMA_MODEL})")
    print("=" * 60)
    print()


def check_status() -> None:
    settings = get_settings()
    print_banner(settings)
    print("Performing pre-flight health checks...\n")

    # 1. Config Validation
    warnings = settings.validate()
    if warnings:
        print("Configuration Warnings:")
        for w in warnings:
            print(f"  [!] {w}")
    else:
        print("  [✓] Configuration: Valid")

    # 2. Ollama Check
    ollama_client = OllamaClient(settings)
    healthy, models, msg = ollama_client.check_health()
    if healthy:
        print(f"  [✓] Ollama Engine: ONLINE ({msg})")
        print(f"      Installed models: {', '.join(models)}")
    else:
        print(f"  [✗] Ollama Engine: WARNING ({msg})")

    # 3. OAuth Files Check
    secret_path = Path(settings.CLIENT_SECRET_FILE)
    token_path = Path(settings.TOKEN_FILE)
    print(f"  [{'✓' if secret_path.exists() else '✗'}] OAuth Client Secret: {secret_path.name}")
    print(f"  [{'✓' if token_path.exists() else '✗'}] Cached OAuth Token: {token_path.name}")

    print("\nPre-flight check completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ChatBrain Local AI YouTube Live Chatbot")
    parser.add_argument("--status", action="store_true", help="Run system health checks and exit")
    parser.add_argument("--all-messages", action="store_true", help="Disable smart filter and process all messages")
    parser.add_argument("--model", type=str, default=None, help="Override configured Ollama model name")

    args = parser.parse_args()
    settings = get_settings()

    if args.status:
        check_status()
        return

    if args.model:
        settings.OLLAMA_MODEL = args.model

    if args.all_messages:
        settings.SMART_REPLY_FILTER = False

    print_banner(settings)

    service = ChatService(settings)
    service.start()


if __name__ == "__main__":
    main()
