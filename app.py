import streamlit as st
import json
import os
import time


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="ChatBrain",
    page_icon="🧠",
    layout="wide"
)


# ==========================================
# TITLE
# ==========================================

st.title("ChatBrain")

st.caption(
    "YouTube Live Chat → Ollama → ChatBrain → Replay"
)


# ==========================================
# FILE
# ==========================================

HISTORY_FILE = "chat_history.jsonl"


# ==========================================
# READ CHAT HISTORY
# ==========================================

def load_messages():

    messages = []

    if not os.path.exists(HISTORY_FILE):
        return messages


    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    data = json.loads(line)

                    messages.append(data)

                except json.JSONDecodeError:

                    continue

    except Exception:

        pass


    return messages


# ==========================================
# LOAD DATA
# ==========================================

messages = load_messages()


# ==========================================
# STATUS
# ==========================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "ChatBrain",
        "Running"
    )


with col2:

    st.metric(
        "Messages",
        len(messages)
    )


with col3:

    st.metric(
        "Ollama",
        "Local"
    )


st.divider()


# ==========================================
# LIVE REPLAY
# ==========================================

st.subheader("Live Chat Replay")


if not messages:

    st.info(
        "Waiting for subscriber messages..."
    )

else:

    # Show newest message first

    for item in reversed(messages):

        author = item.get(
            "author",
            "Unknown"
        )

        message = item.get(
            "message",
            ""
        )

        reply = item.get(
            "reply",
            ""
        )

        timestamp = item.get(
            "timestamp",
            ""
        )


        # ------------------------------
        # Subscriber
        # ------------------------------

        st.markdown(
            f"### {author}"
        )


        st.write(
            f"Subscriber: {message}"
        )


        # ------------------------------
        # ChatBrain
        # ------------------------------

        st.success(
            f"ChatBrain: {reply}"
        )


        st.caption(
            timestamp
        )


        st.divider()


# ==========================================
# AUTO REFRESH
# ==========================================

time.sleep(2)

st.rerun()