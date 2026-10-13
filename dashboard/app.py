"""Streamlit Dashboard for ChatBrain.

Visualizes real-time YouTube live chat interaction history, Ollama status,
and operational telemetry without exposing credentials or tokens.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path if launched from submodule
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
from config.settings import get_settings
from llm.ollama_client import OllamaClient

settings = get_settings()

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title=f"{settings.PROJECT_NAME} Dashboard",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 ChatBrain Dashboard")
st.caption("Live Chat Replay • Local Ollama AI • YouTube Stream Assistant")

# =========================================================
# STATUS CHECKS
# =========================================================

ollama_client = OllamaClient(settings)
ollama_healthy, installed_models, ollama_msg = ollama_client.check_health()


def load_history():
    messages = []
    if not os.path.exists(settings.HISTORY_FILE):
        return messages

    try:
        with open(settings.HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as err:
        st.error(f"Error reading history file: {err}")

    return messages


messages = load_history()
total_messages = len(messages)
replies_sent = sum(1 for m in messages if m.get("posted_to_youtube", False))

# =========================================================
# METRICS ROW
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "ChatBrain Service",
        "Active",
        delta="v" + settings.VERSION,
    )

with col2:
    st.metric(
        "Messages Logged",
        total_messages,
    )

with col3:
    st.metric(
        "Replies Posted",
        replies_sent,
    )

with col4:
    status_label = "Online" if ollama_healthy else "Offline"
    st.metric(
        "Ollama Status",
        status_label,
        delta=settings.OLLAMA_MODEL,
        delta_color="normal" if ollama_healthy else "inverse",
    )

if not ollama_healthy:
    st.warning(f"⚠️ {ollama_msg}")

st.divider()

# =========================================================
# SIDEBAR / CONFIG VIEWER
# =========================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    st.write(f"**Model:** `{settings.OLLAMA_MODEL}`")
    st.write(f"**Ollama Host:** `{settings.OLLAMA_BASE_URL}`")
    st.write(f"**Smart Filter:** `{'Enabled' if settings.SMART_REPLY_FILTER else 'Disabled'}`")
    st.write(f"**Humor Mode:** `{'Enabled' if settings.HUMOR_ENABLED else 'Disabled'}`")
    st.write(f"**Global Cooldown:** `{settings.GLOBAL_REPLY_COOLDOWN_SECONDS}s`")
    st.write(f"**User Cooldown:** `{settings.USER_REPLY_COOLDOWN_SECONDS}s`")
    st.write(f"**Max Reply Length:** `{settings.MAX_REPLY_LENGTH} chars`")

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# =========================================================
# LIVE CHAT REPLAY & FILTERING
# =========================================================

st.subheader("💬 Live Chat Activity")

col_search, col_filter = st.columns([3, 1])

with col_search:
    search_query = st.text_input("Search messages or authors:", placeholder="Search...")

with col_filter:
    filter_choice = st.selectbox(
        "Filter View",
        ["All Interactions", "Only Posted to YouTube", "Ignored / Not Posted"],
    )

# Filter messages
filtered_messages = messages
if filter_choice == "Only Posted to YouTube":
    filtered_messages = [m for m in filtered_messages if m.get("posted_to_youtube", False)]
elif filter_choice == "Ignored / Not Posted":
    filtered_messages = [m for m in filtered_messages if not m.get("posted_to_youtube", False)]

if search_query:
    q = search_query.lower()
    filtered_messages = [
        m for m in filtered_messages
        if q in m.get("author", "").lower() or q in m.get("message", "").lower() or q in m.get("reply", "").lower()
    ]

if not filtered_messages:
    st.info("No chat messages matching the current filter.")
else:
    # Display newest first
    for item in reversed(filtered_messages):
        author = item.get("author", "Unknown")
        user_msg = item.get("message", "")
        reply = item.get("reply", "")
        timestamp = item.get("timestamp", "")
        posted = item.get("posted_to_youtube", False)
        lang = item.get("language", "")
        decision_reason = item.get("decision_reason", "")

        with st.container():
            st.markdown(f"### 👤 {author}")
            st.write(f"**Subscriber:** {user_msg}")

            if reply:
                st.success(f"🤖 **ChatBrain:** {reply}")

            badges = []
            if posted:
                badges.append("🟢 Posted to YouTube")
            else:
                badges.append("⚪ Local Log Only")

            if lang and lang != "unknown":
                badges.append(f"🌐 {lang}")

            if decision_reason:
                badges.append(f"🎯 {decision_reason}")

            badges.append(f"⏱️ {timestamp}")

            st.caption(" • ".join(badges))
            st.divider()
