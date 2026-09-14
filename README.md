# ChatBrain

**AI-powered YouTube Live Chat Assistant using Ollama, Llama 3.2, LangChain, Python, and YouTube Data API v3.**

ChatBrain reads messages from a YouTube Live Chat, generates AI-powered responses using a locally running **Llama 3.2 model through Ollama**, and automatically posts the response back to the YouTube Live Chat.

---

## Features

* Read YouTube Live Chat messages
* Generate responses using local AI
* Powered by Ollama + Llama 3.2
* LangChain integration
* Automatically reply to subscribers
* Reply in the same language as the subscriber
* Supports English, Hindi, Marathi, Hinglish, and mixed languages
* Marathi written in English letters is supported
* Desi and casual conversation style
* Short and natural responses
* Light humor when appropriate
* No voice/TTS
* Save chat history
* Streamlit dashboard
* Google OAuth 2.0 authentication
* Runs locally

---

## Project Workflow

```text
YouTube Live Chat
        ↓
Subscriber Message
        ↓
YouTube Data API v3
        ↓
Python
        ↓
LangChain
        ↓
Ollama
        ↓
Llama 3.2
        ↓
AI Generated Response
        ↓
YouTube Data API
        ↓
YouTube Live Chat
```

### Chat History

```text
Subscriber Message
        ↓
chat_history.jsonl
        ↓
Streamlit Dashboard
```

---

## Tech Stack

| Technology          | Purpose                          |
| ------------------- | -------------------------------- |
| Python              | Main programming language        |
| Ollama              | Local AI model runtime           |
| Llama 3.2           | AI language model                |
| LangChain           | LLM integration                  |
| YouTube Data API v3 | Read and send live chat messages |
| Google OAuth 2.0    | YouTube authentication           |
| Streamlit           | Dashboard                        |
| JSONL               | Chat history storage             |

---

## Project Structure

```text
chat-brain/
│
├── youtube.py
├── app.py
├── requirements.txt
├── run_chatbrain.cmd
├── README.md
├── .gitignore
│
├── client_secret.json
├── token.json
├── .env
└── chat_history.jsonl
```

> `client_secret.json`, `token.json`, `.env`, and `chat_history.jsonl` should remain local and must not be uploaded to GitHub.

---

# Requirements

Before running ChatBrain, install:

* Python 3.10+
* Ollama
* Llama 3.2
* Google Cloud account
* YouTube channel
* YouTube Data API v3

---

# Installation

## 1. Install Ollama

Download Ollama:

https://ollama.com/

Check the installation:

```bash
ollama --version
```

---

## 2. Download Llama 3.2

```bash
ollama pull llama3.2
```

Check installed models:

```bash
ollama list
```

Test the model:

```bash
ollama run llama3.2
```

---

## 3. Clone the Repository

```bash
git clone https://github.com/Sp-4030/chat-brain.git
```

Go to the project directory:

```bash
cd chat-brain
```

---

## 4. Create Virtual Environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## 5. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

Or install manually:

```bash
python -m pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client langchain-ollama streamlit langchain
```

---

# YouTube API Setup

ChatBrain uses the **YouTube Data API v3** to read and send Live Chat messages.

## 1. Create Google Cloud Project

Open:

https://console.cloud.google.com/

Create a project.

Example:

```text
ChatBrain
```

---

## 2. Enable YouTube Data API v3

Go to:

```text
Google Cloud Console
        ↓
APIs & Services
        ↓
Library
        ↓
YouTube Data API v3
        ↓
Enable
```

---

## 3. Create OAuth Client

Go to:

```text
APIs & Services
        ↓
Credentials
        ↓
Create Credentials
        ↓
OAuth Client ID
```

Select:

```text
Desktop app
```

Download the JSON file.

Rename it:

```text
client_secret.json
```

Place it inside the project folder:

```text
chat-brain/
├── youtube.py
├── app.py
├── client_secret.json
└── ...
```

---

# OAuth Permission

ChatBrain uses:

```text
https://www.googleapis.com/auth/youtube.force-ssl
```

This allows the application to interact with YouTube on behalf of the authenticated account.

---

# First Run

Start your YouTube Live Stream first.

If an old `token.json` exists, delete it for the first setup or whenever you need to re-authorize with the required permission.

Run:

```bash
python youtube.py
```

A Google login window will open.

Sign in with the YouTube account that owns the Live Stream and allow the requested permissions.

After successful authentication, ChatBrain creates:

```text
token.json
```

---

# Start ChatBrain

Start your YouTube Live Stream.

Then run:

```bash
python youtube.py
```

You should see:

```text
========================================
          CHATBRAIN STARTING
========================================

YouTube OAuth: CONNECTED

Searching for active YouTube Live...

Live Chat ID found successfully!

========================================
        CHATBRAIN IS CONNECTED
========================================

YouTube Live : CONNECTED
Ollama       : CONNECTED
Model        : llama3.2
YouTube Reply: ENABLED

Waiting for subscriber messages...
```

Now ChatBrain will monitor the Live Chat.

---

# Example

### Subscriber

```text
Python kya hai?
```

### ChatBrain

```text
Python ek programming language hai bhai. Beginners ke liye iska syntax kaafi simple hai.
```

---

### Subscriber

```text
Python म्हणजे काय?
```

### ChatBrain

```text
Python ही एक programming language आहे. Beginners साठी तिचा syntax simple आहे.
```

---

### Subscriber

```text
Python kay aahe?
```

### ChatBrain

```text
Python ek programming language aahe bhai. Beginners sathi ti easy aahe.
```

---

### Subscriber

```text
What is Python?
```

### ChatBrain

```text
Python is a programming language known for its simple and readable syntax.
```

---

# Streamlit Dashboard

ChatBrain also includes a Streamlit dashboard.

Run:

```bash
python -m streamlit run app.py
```

The dashboard can display saved ChatBrain conversations and chat activity.

---

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
ollama pull llama3.2
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
# Chat-Brain
