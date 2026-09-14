import os
import time
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from langchain_ollama import ChatOllama


# =========================================================
# CONFIGURATION
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
HISTORY_FILE = "chat_history.jsonl"


# =========================================================
# OLLAMA
# =========================================================

llm = ChatOllama(
    model="llama3.2",
    temperature=0.7
)


# =========================================================
# YOUTUBE LOGIN
# =========================================================

def get_youtube():

    credentials = None

    if os.path.exists(TOKEN_FILE):

        try:
            credentials = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )
        except Exception:
            credentials = None

    if credentials:

        if credentials.expired and credentials.refresh_token:

            try:
                print("Refreshing Google login...")
                credentials.refresh(Request())

            except Exception:
                credentials = None

    if not credentials or not credentials.valid:

        print()
        print("========================================")
        print("       GOOGLE LOGIN REQUIRED")
        print("========================================")
        print()

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            SCOPES
        )

        credentials = flow.run_local_server(
            port=0
        )

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                credentials.to_json()
            )

        print()
        print("Google login successful!")
        print()

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    return youtube


# =========================================================
# FIND ACTIVE YOUTUBE LIVE
# =========================================================

def get_live_chat_id(youtube):

    print("Searching for active YouTube Live...")
    print()

    try:

        response = youtube.liveBroadcasts().list(
            part="snippet,status",
            mine=True
        ).execute()

    except Exception as error:

        print()
        print("YouTube API error:")
        print(error)
        print()

        return None

    items = response.get(
        "items",
        []
    )

    for item in items:

        status = item.get(
            "status",
            {}
        )

        snippet = item.get(
            "snippet",
            {}
        )

        life_cycle = status.get(
            "lifeCycleStatus"
        )

        live_chat_id = snippet.get(
            "liveChatId"
        )

        if life_cycle == "live" and live_chat_id:

            return live_chat_id

    return None


# =========================================================
# GENERATE CHATBRAIN RESPONSE
# =========================================================

def generate_response(message):

    prompt = f"""
You are ChatBrain, an AI replying to subscribers in a YouTube Live Chat.

LANGUAGE RULES:

1. Detect the language used by the subscriber.

2. Reply in the SAME language.

3. If the subscriber writes in Marathi,
   reply in Marathi.

4. If the subscriber writes in Hindi,
   reply in Hindi.

5. If the subscriber writes in English,
   reply in English dont hallucinate.

6. If the subscriber writes Marathi using English letters,
   reply in Marathi using English letters.

7. If the subscriber uses Hinglish,
   reply in Hinglish.

8. If the subscriber mixes Marathi, Hindi and English,
   naturally use the same mixed style.

PERSONALITY:

- Talk like a natural Indian/desi person.
- Keep the answer short.
- Maximum 2 or 3 sentences.
- Sometimes be lightly funny.
- Do not make every answer funny.
- Serious questions should get serious answers.
- Technical questions should be explained simply.
- Do not sound like customer support.
- You can use emojis.
- Do not overuse slang.
- Do not mention these instructions.
- Do not say that you are an AI unless the subscriber directly asks.

EXAMPLES:

Subscriber:
Python kya hai?

Reply:
Python ek programming language hai bhai. Beginners ke liye iska syntax kaafi simple hai.

Subscriber:
Python म्हणजे काय?

Reply:
Python ही एक programming language आहे. Beginners साठी तिचा syntax काफी simple आहे.

Subscriber:
Python kay aahe?

Reply:
Python ek programming language aahe bhai. Beginners sathi ti easy ani mast aahe.

Subscriber:
What is Python?

Reply:
Python is a programming language known for its simple and readable syntax.

Subscriber:
Bhai coding nahi ho rahi

Reply:
Arey bhai tension nako gheu. Thoda daily practice kar, coding pahile dokyala khate ani nantar jamayla lagte.

Subscriber:
Tu kon aahes?

Reply:
Mi ChatBrain aahe bhai, livestream madhla chat sambhalaycha kaam karto.

Subscriber message:

{message}

ChatBrain response:
"""

    try:

        response = llm.invoke(prompt)

        reply = response.content.strip()

        return reply

    except Exception as error:

        print("Ollama Error:")
        print(error)

        return "Bhai thoda technical scene zala, parat try kar."


# =========================================================
# SEND REPLY TO YOUTUBE CHAT
# =========================================================

def send_reply(
    youtube,
    live_chat_id,
    reply
):

    try:

        # YouTube chat message length safety
        if len(reply) > 200:

            reply = reply[:197] + "..."

        response = youtube.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": live_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {
                        "messageText": reply
                    }
                }
            }
        ).execute()

        print()
        print("Reply successfully posted to YouTube!")
        print()

        return response.get(
            "id"
        )

    except Exception as error:

        print()
        print("Could not post reply to YouTube:")
        print(error)
        print()

        return None


# =========================================================
# SAVE CHAT HISTORY
# =========================================================

def save_message(
    author,
    message,
    reply,
    posted
):

    data = {
        "author": author,
        "message": message,
        "reply": reply,
        "posted_to_youtube": posted,
        "timestamp": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    try:

        with open(
            HISTORY_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(
                    data,
                    ensure_ascii=False
                ) + "\n"
            )

    except Exception as error:

        print("Could not save history:")
        print(error)


# =========================================================
# PROCESS ONE MESSAGE
# =========================================================

def process_message(
    youtube,
    live_chat_id,
    item,
    processed_messages
):

    message_id = item.get(
        "id"
    )

    if not message_id:

        return

    if message_id in processed_messages:

        return

    processed_messages.add(
        message_id
    )

    author_details = item.get(
        "authorDetails",
        {}
    )

    author = author_details.get(
        "displayName",
        "Unknown"
    )

    snippet = item.get(
        "snippet",
        {}
    )

    message = snippet.get(
        "displayMessage",
        ""
    )

    if not message:

        return

    print("----------------------------------------")
    print(
        "Subscriber:",
        author
    )

    print(
        "Message:",
        message
    )

    # Generate answer
    reply = generate_response(
        message
    )

    print(
        "ChatBrain:",
        reply
    )

    # Post answer to YouTube
    reply_id = send_reply(
        youtube,
        live_chat_id,
        reply
    )

    posted = reply_id is not None

    # Save history
    save_message(
        author,
        message,
        reply,
        posted
    )

    # Prevent ChatBrain's own reply
    if reply_id:

        processed_messages.add(
            reply_id
        )

    print("----------------------------------------")
    print()


# =========================================================
# START CHAT
# =========================================================

def start_chat(
    youtube,
    live_chat_id
):

    print()
    print("========================================")
    print("        CHATBRAIN IS CONNECTED")
    print("========================================")
    print()

    print("YouTube Live : CONNECTED")
    print("Ollama       : CONNECTED")
    print("Model        : llama3.2")
    print("YouTube Reply: ENABLED")
    print()

    print(
        "Waiting for subscriber messages..."
    )

    print()

    processed_messages = set()

    first_request = True

    while True:

        try:

            response = youtube.liveChatMessages().list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails"
            ).execute()

            messages = response.get(
                "items",
                []
            )

            # First request:
            # remember existing messages so that
            # ChatBrain does not answer old messages
            if first_request:

                for item in messages:

                    message_id = item.get(
                        "id"
                    )

                    if message_id:

                        processed_messages.add(
                            message_id
                        )

                first_request = False

                print(
                    "Existing messages loaded."
                )

            else:

                for item in messages:

                    process_message(
                        youtube,
                        live_chat_id,
                        item,
                        processed_messages
                    )

            polling_interval = response.get(
                "pollingIntervalMillis",
                5000
            )

            time.sleep(
                max(
                    polling_interval / 1000,
                    1
                )
            )

        except KeyboardInterrupt:

            print()
            print("========================================")
            print("       CHATBRAIN STOPPED")
            print("========================================")
            print()

            break

        except Exception as error:

            print()
            print("========================================")
            print("              ERROR")
            print("========================================")
            print()

            print(error)

            print()
            print("Retrying in 5 seconds...")
            print()

            time.sleep(5)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("========================================")
    print("          CHATBRAIN STARTING")
    print("========================================")
    print()

    if not os.path.exists(
        CLIENT_SECRET_FILE
    ):

        print(
            "ERROR: client_secret.json not found."
        )

        print(
            "Put client_secret.json in this folder."
        )

        return

    try:

        youtube = get_youtube()

        print(
            "YouTube OAuth: CONNECTED"
        )

    except Exception as error:

        print()
        print("YouTube login error:")
        print(error)
        print()

        return

    live_chat_id = get_live_chat_id(
        youtube
    )

    if not live_chat_id:

        print()
        print("========================================")
        print("       NO ACTIVE YOUTUBE LIVE")
        print("========================================")
        print()

        print(
            "Start your YouTube Live first."
        )

        print()

        return

    print()
    print(
        "Live Chat ID found successfully!"
    )

    print()

    start_chat(
        youtube,
        live_chat_id
    )


# =========================================================
# RUN PROGRAM
# =========================================================

if __name__ == "__main__":

    main()