# 🧠 ChatBrain — Local AI YouTube Live Chat Assistant

ChatBrain is a local AI-powered chatbot designed to automatically interact with viewers on YouTube Live Chat. Powered by local LLMs via **Ollama**, it provides natural, friendly, and culturally nuanced (Desi/Marathi/Hindi/Hinglish/English) live replies while running 100% locally on your machine with zero external AI API costs.

---

## 🌟 Key Features

- **Local AI Inference**: Powered by local Ollama models (default: `llama3.2:latest`) — no OpenAI, Anthropic, or paid cloud AI API keys required.
- **Multilingual & Script-Aware**: Dynamically detects and responds in the viewer's language and script:
  - Marathi (Devanagari: मराठी & Roman: e.g. *kay chalalay bhava*)
  - Hindi (Devanagari: हिंदी)
  - Hinglish (Roman Hindi: e.g. *kya haal hai bhai*)
  - English
- **Natural Desi Personality**: Stream-tailored conversational tone featuring friendly banter, Kolhapur/Maharashtra touches, and BCA/coding life tropes.
- **Modular Event-Driven Architecture**: Decoupled message reader, normalization, duplicate filter, reply decision engine, context manager, and YouTube dispatcher.
- **API Quota & Rate-Limit Protection**: 
  - YouTube-mandated polling interval adherence.
  - Global reply cooldown (configurable).
  - Per-user rate-limiting and sliding window cooldown.
  - Duplicate message filtering and duplicate reply prevention.
- **Smart Reply Filtering**: Only processes questions or direct mentions (`@chatbrain`) during busy streams, saving API quota.
- **Isolated Conversation Memory**: Maintains short-term conversational context per viewer for natural follow-ups without context bleed between viewers.
- **Streamlit Replay Dashboard**: Real-time interface to inspect live chats, model responses, delivery status, and operational metrics.
- **Windows Launcher**: Simple `.cmd` scripts with automatic virtual environment detection.

---

## 🏗️ Architecture & Processing Pipeline

### Directory Structure

```text
chat-brain/
├── main.py                     # Unified CLI entry point & health check
├── app.py                      # Streamlit dashboard launcher
├── brain.py                    # Backwards-compatible AI response generator
├── youtube.py                  # Backwards-compatible YouTube integration
├── config/
│   ├── __init__.py
│   └── settings.py             # Centralized settings & environment loading
├── youtube/
│   ├── __init__.py
│   ├── client.py               # OAuth 2.0 lifecycle & service builder
│   ├── live_chat_reader.py     # Live broadcast finder, message polling & pagination
│   └── message_sender.py       # Message truncation & YouTube liveChat insert
├── events/
│   ├── __init__.py
│   ├── base_event.py           # Base event dataclass
│   ├── chat_message_event.py   # Normalized chat message event
│   └── event_bus.py            # Thread-safe pub/sub event dispatcher
├── listeners/
│   ├── __init__.py
│   └── chat_message_listener.py# Event listener orchestrating response pipeline
├── context/
│   ├── __init__.py
│   └── conversation_context.py # Per-user & stream-wide bounded conversation turns
├── identity/
│   ├── __init__.py
│   └── user_identity.py        # Stable channel tracking, bot self-check & cooldowns
├── decision/
│   ├── __init__.py
│   ├── reply_decision.py       # Reply eligibility, mention & question evaluation
│   └── safety_rules.py         # Spam prevention, link filters & blocked keywords
├── comedy/
│   ├── __init__.py
│   └── humor_engine.py         # Light desi humor hints & anti-repetition tracker
├── memory/
│   ├── __init__.py
│   └── conversation_memory.py  # Bounded deduplication cache & JSONL persistence
├── learning/
│   ├── __init__.py
│   └── interaction_feedback.py # Operational telemetry & latency tracker
├── llm/
│   ├── __init__.py
│   ├── ollama_client.py        # Reusable Ollama client with health check & retry
│   └── prompt_builder.py       # Persona prompt generator & output sanitizer
├── dashboard/
│   ├── __init__.py
│   └── app.py                  # Streamlit visual dashboard
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Sanitized structured logging (token masking)
│   └── language_detector.py    # Lightweight script & lexical language detector
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── start_chatbrain.cmd         # Windows launcher with virtualenv auto-detection
├── run_chatbrain.cmd           # Alternate Windows launcher
└── README.md
```

### Event-Driven Pipeline Flow

```text
YouTube Live Stream
        ↓
[LiveChatReader] (Polls liveChatMessages.list respecting quota interval)
        ↓
[ChatMessageEvent] (Normalized with author ID, display name, text, metadata)
        ↓
[EventBus] (Dispatches to registered subscribers)
        ↓
[ChatMessageListener]
        ↓
├── [ConversationMemory] (Check if message ID was already processed)
├── [UserIdentityManager] (Update viewer history; verify not bot's own message)
├── [ReplyDecisionEngine] (Check smart filter, question words, global & user cooldowns)
├── [LanguageDetector] (Identify Marathi Devanagari/Roman, Hindi, Hinglish, English)
├── [ConversationContextManager] (Retrieve recent context for this viewer)
├── [HumorEngine] (Determine if light banter/humor fits)
├── [PromptBuilder] (Assemble persona prompt + guardrails)
├── [OllamaClient] (Local inference via Ollama with retry & timeout protection)
├── [PromptBuilder.clean_reply] (Strip prefixes, deduplicate, limit length)
├── [YouTubeMessageSender] (Post text reply to YouTube Live Chat)
└── [ConversationMemory] (Save record to chat_history.jsonl)
```

---

## ⚙️ Prerequisites & Setup

### 1. Python Environment

- Python 3.10 or higher.
- Create and activate a virtual environment:

```cmd
cd C:\Users\Shantanu\Desktop\chat-brain
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```cmd
python -m pip install -r requirements.txt
```

Installed packages:
- `streamlit`: Dashboard interface.
- `langchain-ollama`: Ollama local LLM client.
- `google-api-python-client`: Official YouTube Data API v3 library.
- `google-auth-oauthlib`: Google OAuth 2.0 flow for desktop apps.
- `google-auth-httplib2`: Google authentication HTTP transport.
- `python-dotenv`: Environment configuration manager.

### 3. Ollama Installation & Model Download

1. Download and install Ollama from [ollama.com](https://ollama.com/).
2. Pull the default model (or any model of your choice):

```cmd
ollama pull llama3.2:latest
```

3. Ensure Ollama is running (`ollama serve` or Ollama desktop app active).

### 4. Google YouTube OAuth Setup

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `ChatBrain`).
3. Under **APIs & Services > Library**, search for and enable **YouTube Data API v3**.
4. Under **APIs & Services > Credentials**, create credentials:
   - Type: **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `ChatBrain Client`
5. Download the JSON credentials file and place it in the project root named:
   ```text
   client_secret.json
   ```
6. On first launch, a browser window will automatically open asking you to sign in with your YouTube Google account to grant live chat access. The resulting token is saved locally to `token.json`.

---

## 🚀 Running ChatBrain

### Pre-flight Health Check
Verify your setup without starting YouTube polling:

```cmd
python main.py --status
```

### Option A: Using Windows Launcher Scripts

Double-click either launcher script in the project directory:
- `start_chatbrain.cmd` (Recommended): Auto-detects virtual environment, launches ChatBrain in one console window and Streamlit Dashboard in another.
- `run_chatbrain.cmd`: Legacy launcher script.

### Option B: Running from Terminal

1. **Start the ChatBrain Service:**
   ```cmd
   python main.py
   ```
   *Optional CLI flags:*
   - `--all-messages`: Reply to all conversational messages instead of only questions/mentions.
   - `--model mistral:latest`: Override the Ollama model on startup.

2. **Start the Dashboard (in a separate terminal window):**
   ```cmd
   streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## 🔧 Configuration Options

Create or update your `.env` file (see `.env.example` for reference):

| Setting | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:latest` | Local LLM model name |
| `OLLAMA_TIMEOUT` | `30.0` | Maximum inference timeout (seconds) |
| `OLLAMA_TEMPERATURE` | `0.8` | LLM creativity / sampling temperature |
| `MAX_REPLY_LENGTH` | `200` | Maximum response character length |
| `SMART_REPLY_FILTER` | `true` | When true, only replies to mentions and questions |
| `GLOBAL_REPLY_COOLDOWN_SECONDS` | `3.0` | Minimum interval between any bot replies |
| `USER_REPLY_COOLDOWN_SECONDS` | `10.0` | Minimum cooldown before replying to the same user |
| `HUMOR_ENABLED` | `true` | Enables light desi banter |
| `HUMOR_INTENSITY` | `0.7` | Humor frequency (0.0 to 1.0) |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HISTORY_FILE` | `chat_history.jsonl` | File path for persistent chat logs |

---

## 🛑 How to Stop the Application

- In terminal windows running `main.py` or `youtube.py`, press **Ctrl + C**. The bot will display a session summary and cleanly exit.
- In terminal windows running Streamlit, press **Ctrl + C**.

---

## ⚠️ Important Notes & Limitations

- **YouTube Daily Quota**: YouTube Data API v3 has a default quota of 10,000 units per day. Polling live chat costs approximately 1-5 units per call. ChatBrain adheres strictly to YouTube's recommended `pollingIntervalMillis` and smart reply filtering to preserve quota.
- **Active Live Broadcast Required**: ChatBrain looks for a broadcast whose status is actively `"live"`. Ensure your YouTube stream is live before starting the service.
- **Security & Privacy**: Never commit `client_secret.json`, `token.json`, or `.env` to public repositories. All tokens and secrets are automatically masked in log outputs.
- **Testing Exclusion**: No runtime automated tests were executed during this refactoring. Verify local Ollama and YouTube connectivity using `python main.py --status`.
