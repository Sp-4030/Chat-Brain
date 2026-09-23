# 🧠🤖Chat-Brain🧠🤖

ChatBrain is a local AI-powered YouTube Live Chat assistant. It watches a live stream, filters relevant subscriber messages, sends them to a local Ollama model, and posts a short conversational reply back into chat.

The current version uses a lightweight local model configured in `brain.py` and includes a Streamlit dashboard to replay saved messages.

## Features

- Reads YouTube Live Chat messages
- Detects likely questions or mentions using a smart reply filter
- Sends messages to a local LLM through Ollama
- Replies in a natural, short, conversational style
- Handles English, Hindi, Hinglish, Marathi, and mixed-language chat
- Saves chat history in JSONL format
- Shows the replay dashboard in Streamlit
- Uses Google OAuth to authenticate with YouTube
- Runs locally without sending chat data to a remote AI service

## Project Flow

```text
YouTube Live Chat
        ↓
Subscriber message
        ↓
YouTube Data API v3
        ↓
ChatBrain (youtube.py)
        ↓
Local LLM via Ollama
        ↓
Short AI response
        ↓
Reply posted back to YouTube Live Chat
```

The app also logs chat activity for later viewing in the Streamlit dashboard:

```text
YouTube message
        ↓
chat_history.jsonl
        ↓
Streamlit dashboard
```

## Tech Stack

- Python
- Google YouTube Data API v3
- Google OAuth 2.0
- Ollama
- LangChain + `langchain-ollama`
- Streamlit
- JSONL for chat history

## Project Structure

```text
chat-brain/
├── app.py                # Streamlit dashboard
├── brain.py              # LLM prompt + response generation
├── youtube.py            # YouTube listener and reply logic
├── requirements.txt      # Python dependencies
├── run_chatbrain.cmd     # Windows launcher
├── run_chatbrain.sh      # macOS/Linux launcher
├── README.md
├── chat_history.jsonl   # Local chat log
├── client_secret.json    # Google OAuth client file (local only)
├── token.json            # YouTube auth token (local only)
└── .gitignore
```

> Keep `client_secret.json`, `token.json`, and `chat_history.jsonl` local to your machine. Do not add them to GitHub if you do not want to share credentials or local chat data.

## Requirements

Before running the app, install:

- Python 3.10+
- Ollama
- A YouTube account with a live stream
- Google Cloud project with YouTube Data API enabled

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Sp-4030/Chat-Brain.git
cd chat-brain
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

The current dependency set includes:

```bash
streamlit
langchain-ollama
google-api-python-client
google-auth-oauthlib
google-auth-httplib2
python-dotenv
```

### 4. Install Ollama and pull a model

Download Ollama from:

https://ollama.com/

Verify it is installed:

```bash
ollama --version
```

Pull the model used by the app:

```bash
ollama pull llama3.2:latest
```

The current model is configured as `llama3.2:latest` in `brain.py`. If you want to use a different Ollama model, update the `MODEL_NAME` value there and pull that model first.

## Google YouTube Setup

### 1. Create a Google Cloud project

Go to:

https://console.cloud.google.com/

Create a new project and name it however you like.

### 2. Enable the YouTube Data API

In Google Cloud Console:

- APIs & Services
- Library
- Search for `YouTube Data API v3`
- Click Enable

### 3. Create OAuth credentials

In Google Cloud Console:

- APIs & Services
- Credentials
- Create Credentials
- OAuth client ID
- Application type: Desktop app

Download the generated JSON file and rename it to:

```text
client_secret.json
```

Place it in the project root.

### 4. Required OAuth scope

This app uses:

```text
https://www.googleapis.com/auth/youtube.force-ssl
```

This grants permission to read and write YouTube Live Chat messages for the authenticated channel.

## Running the app

### Option 1: use the launcher scripts

Windows:

```cmd
run_chatbrain.cmd
```

macOS/Linux:

```bash
chmod +x run_chatbrain.sh
./run_chatbrain.sh
```

These scripts start:

- the YouTube live chat listener in `youtube.py`
- the Streamlit dashboard in `app.py`

The launcher opens separate terminal windows for both processes. Keep both processes running while using ChatBrain.

### Option 2: run manually

Start the chat bot:

```bash
python youtube.py
```

Start the dashboard in another terminal:

```bash
python -m streamlit run app.py
```

## First run

1. Start a YouTube Live stream on the channel you want to monitor.
2. Run the app.
3. Sign in with the YouTube account that owns the stream when Google prompts you.
4. The app creates a local `token.json` file after successful authentication.
5. Once connected, it will monitor the live chat and reply when conditions match.

If you need to re-authorize, delete the existing `token.json` and run again.

## Dashboard

Open the Streamlit dashboard at:

```text
http://localhost:8501
```

The dashboard shows the saved chat history and replay of messages with the AI reply status.

The dashboard reads `chat_history.jsonl` from the project directory. It refreshes when you click **Refresh Chat**; it does not replace the YouTube listener.

## Notes

- The default model in `brain.py` is `llama3.2:latest`.
- The bot is intentionally conservative: it only replies when a message looks like a question, includes a bot mention, or otherwise fits the reply filter.
- Responses are intentionally short and conversational to fit a live chat environment.
- This is a local-first project; it does not require a hosted LLM backend.

## Example replies

Subscriber:

```text
Python kya hai?
```

ChatBrain:

```text
Python ek programming language hai bhai. Beginners ke liye iska syntax kaafi simple hai.
```

Subscriber:

```text
What is Python?
```

ChatBrain:

```text
Python is a programming language known for its simple and readable syntax.
```


# One-Click Startup

Windows users can use:

```text
run_chatbrain.cmd
```

Double-click the file to start:

```text
YouTube ChatBrain
        +
Streamlit Dashboard
```

---

# Chat History

ChatBrain saves conversations in:

```text
chat_history.jsonl
```

Example:

```json
{
  "author": "Subscriber",
  "message": "Python kya hai?",
  "reply": "Python ek programming language hai bhai.",
  "posted_to_youtube": true,
  "timestamp": "2026-09-14 17:00:00"
}
```

---

# Language Support

ChatBrain is designed to respond in the same language and style used by the subscriber.

### Supported styles

* English
* Hindi
* Marathi
* Hinglish
* Marathi in English letters
* Mixed Marathi + Hindi + English

Example:

```text
Subscriber:
Bhai coding nahi ho rahi

ChatBrain:
Arey bhai tension nako gheu. Thoda daily practice kar, coding jamayla lagel.
```

---

# Security

Never upload these files to GitHub:

```text
client_secret.json
token.json
.env
chat_history.jsonl
```

These files are excluded through `.gitignore`.

Never share:

* OAuth client secrets
* Access tokens
* Refresh tokens
* API credentials

GitHub also recommends repository security features such as secret scanning and push protection for public repositories.

---

# Troubleshooting

## Ollama is not recognized

Check:

```bash
ollama --version
```

If it is not recognized, install Ollama and restart the terminal.

---

## Llama 3.2 not found

Run:

```bash
ollama pull llama3.2:latest
```

Then:

```bash
ollama list
```

---

## Google authentication problem

Delete:

```text
token.json
```

Then run:

```bash
python youtube.py
```

and complete Google authentication again.

---

## No active YouTube Live

ChatBrain requires an active YouTube Live Stream.

Start the livestream first and then run:

```bash
python youtube.py
```

---

## Streamlit is not recognized

Use:

```bash
python -m streamlit run app.py
```

instead of:

```bash
streamlit run app.py
```

---

# Future Improvements

* Better language detection
* Subscriber name personalization
* Spam filtering
* Automatic moderation
* Admin commands
* Conversation memory
* Multiple Ollama models
* Better Streamlit analytics
* Custom AI personalities
* Docker support

---

# Author

**Shantanu Patil**

BCA Graduate

GitHub:
https://github.com/Sp-4030

---

## License

This project is created for educational and personal use.
# 🧠🤖Chat-Brain🧠🤖
