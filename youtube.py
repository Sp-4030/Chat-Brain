import os
import time
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from brain import generate_response


# =========================================================
# CONFIGURATION
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
HISTORY_FILE = "chat_history.jsonl"

MAX_REPLY_LENGTH = 200


MIN_POLL_SECONDS = 1

ERROR_RETRY_SECONDS = 10


# =========================================================
# QUOTA-SAVING FILTER
# =========================================================

SMART_REPLY_FILTER = True


BOT_NAMES = [
    "chatbrain",
    "@chatbrain"
]


QUESTION_WORDS = [
    # English
    "what",
    "why",
    "how",
    "who",
    "when",
    "where",
    "which",
    "can",
    "could",
    "should",
    "is",
    "are",
    "do",
    "does",

    # Hindi / Hinglish
    "kya",
    "kaise",
    "kyu",
    "kyun",
    "kon",
    "kaun",
    "kab",
    "kaha",
    "kahan",
    "hai",
    "he",

    # Marathi / Roman Marathi
    "kay",
    "kas",
    "kasa",
    "kashi",
    "ka",
    "kuthe",
    "kadhi",
    "kon",
    "kaay"
]


# =========================================================
# YOUTUBE LOGIN
# =========================================================

def get_youtube():

    credentials = None

    # -----------------------------------------
    # Load existing token
    # -----------------------------------------

    if os.path.exists(TOKEN_FILE):

        try:

            credentials = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )

        except Exception as error:

            print("Could not load token:")
            print(error)

            credentials = None

    # -----------------------------------------
    # Refresh token
    # -----------------------------------------

    if credentials:

        if (
            credentials.expired
            and credentials.refresh_token
        ):

            try:

                print("Refreshing Google login...")

                credentials.refresh(
                    Request()
                )

            except Exception as error:

                print("Token refresh failed:")
                print(error)

                credentials = None

    # -----------------------------------------
    # New Google login
    # -----------------------------------------

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

    # -----------------------------------------
    # Build YouTube API client
    # -----------------------------------------

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )

    return youtube


# =========================================================
# FIND ACTIVE YOUTUBE LIVE
# =========================================================

def get_live_chat_id(youtube):

    print(
        "Searching for active YouTube Live..."
    )

    print()

    try:

        # -----------------------------------------
        # This request happens only once at startup.
        # -----------------------------------------

        response = youtube.liveBroadcasts().list(
            part="snippet,status",
            mine=True,
            maxResults=10
        ).execute()

    except HttpError as error:

        print()
        print("YouTube API error:")
        print(error)
        print()

        if "quotaExceeded" in str(error):

            print(
                "!!! DAILY YOUTUBE QUOTA EXCEEDED !!!"
            )

        return None

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

        if (
            life_cycle == "live"
            and live_chat_id
        ):

            return live_chat_id

    return None


# =========================================================
# SMART REPLY FILTER
# =========================================================

def should_reply(message):

    text = message.strip().lower()

    if not text:

        return False

    # -----------------------------------------
    # Direct ChatBrain mention
    # -----------------------------------------

    for bot_name in BOT_NAMES:

        if bot_name in text:

            return True

    # -----------------------------------------
    # Question mark
    # -----------------------------------------

    if "?" in text:

        return True

    # -----------------------------------------
    # Question words
    # -----------------------------------------

    words = text.split()

    for word in QUESTION_WORDS:

        if word in words:

            return True

    return False


# =========================================================
# SEND REPLY TO YOUTUBE
# =========================================================

def send_reply(
    youtube,
    live_chat_id,
    reply
):

    try:

        # -----------------------------------------
        # Length safety
        # -----------------------------------------

        if len(reply) > MAX_REPLY_LENGTH:

            reply = (
                reply[:MAX_REPLY_LENGTH - 3]
                + "..."
            )

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
        print(
            "Reply successfully posted!"
        )
        print()

        return response.get(
            "id"
        )

    except HttpError as error:

        print()
        print(
            "Could not post reply:"
        )

        print(error)

        print()

        if "quotaExceeded" in str(error):

            print(
                "!!! DAILY YOUTUBE QUOTA EXCEEDED !!!"
            )

        return None

    except Exception as error:

        print()
        print(
            "Could not post reply:"
        )

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
                )
                + "\n"
            )

    except Exception as error:

        print(
            "Could not save history:"
        )

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

    # -----------------------------------------
    # Duplicate protection
    # -----------------------------------------

    if message_id in processed_messages:

        return

    processed_messages.add(
        message_id
    )

    # -----------------------------------------
    # Author
    # -----------------------------------------

    author_details = item.get(
        "authorDetails",
        {}
    )

    author = author_details.get(
        "displayName",
        "Unknown"
    )

    # -----------------------------------------
    # Message
    # -----------------------------------------

    snippet = item.get(
        "snippet",
        {}
    )

    message = snippet.get(
        "displayMessage",
        ""
    ).strip()

    if not message:

        return

    # -----------------------------------------
    # Print subscriber message
    # -----------------------------------------

    print("----------------------------------------")

    print(
        "Subscriber:",
        author
    )

    print(
        "Message:",
        message
    )

    # -----------------------------------------
    # QUOTA SAVING FILTER
    #
    # If message is not a question and does
    # not mention ChatBrain, do nothing.
    #
    # No Ollama call.
    # No YouTube insert call.
    # -----------------------------------------

    if SMART_REPLY_FILTER:

        if not should_reply(message):

            print(
                "ChatBrain: Ignored "
                "(not a question/request)"
            )

            print(
                "----------------------------------------"
            )

            print()

            return

    # -----------------------------------------
    # Generate response using local Ollama
    # -----------------------------------------

    reply = generate_response(
        message
    )

    print(
        "ChatBrain:",
        reply
    )

    # -----------------------------------------
    # Post response
    # -----------------------------------------

    reply_id = send_reply(
        youtube,
        live_chat_id,
        reply
    )

    posted = (
        reply_id is not None
    )

    # -----------------------------------------
    # Save history
    # -----------------------------------------

    save_message(
        author,
        message,
        reply,
        posted
    )

    # -----------------------------------------
    # Remember bot reply
    # -----------------------------------------

    if reply_id:

        processed_messages.add(
            reply_id
        )

    print(
        "Posted:",
        posted
    )

    print(
        "----------------------------------------"
    )

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

    print(
        "YouTube : CONNECTED"
    )

    print(
        "Ollama  : CONNECTED"
    )

    print(
        "Reply   : ENABLED"
    )

    print(
        "Filter  :",
        SMART_REPLY_FILTER
    )

    print()

    print(
        "Waiting for subscriber messages..."
    )

    print()

    # -----------------------------------------
    # Already processed messages
    # -----------------------------------------

    processed_messages = set()

    # -----------------------------------------
    # First request
    # -----------------------------------------

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

            # -----------------------------------------
            # First request:
            # remember existing messages.
            #
            # Do NOT reply to old messages.
            # -----------------------------------------

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

            # -----------------------------------------
            # Process new messages
            # -----------------------------------------

            else:

                for item in messages:

                    process_message(
                        youtube,
                        live_chat_id,
                        item,
                        processed_messages
                    )

            # -----------------------------------------
            # IMPORTANT:
            #
            # YouTube tells us when to poll again.
            #
            # Do NOT replace this with 1 or 2 sec.
            # -----------------------------------------

            polling_interval = response.get(
                "pollingIntervalMillis",
                5000
            )

            polling_seconds = max(
                polling_interval / 1000,
                MIN_POLL_SECONDS
            )

        

            time.sleep(
                polling_seconds
            )

        except KeyboardInterrupt:

            print()
            print("========================================")
            print("       CHATBRAIN STOPPED")
            print("========================================")
            print()

            break

        except HttpError as error:

            print()
            print("========================================")
            print("          YOUTUBE API ERROR")
            print("========================================")
            print()

            print(error)

            # -----------------------------------------
            # STOP on quota exhaustion.
            # -----------------------------------------

            if "quotaExceeded" in str(error):

                print()
                print(
                    "YouTube daily quota is exhausted."
                )

                print(
                    "ChatBrain stopped."
                )

                print()

                break

            print()
            print(
                f"Retrying in "
                f"{ERROR_RETRY_SECONDS} seconds..."
            )

            print()

            time.sleep(
                ERROR_RETRY_SECONDS
            )

        except Exception as error:

            print()
            print("========================================")
            print("              ERROR")
            print("========================================")
            print()

            print(error)

            print()
            print(
                f"Retrying in "
                f"{ERROR_RETRY_SECONDS} seconds..."
            )

            print()

            time.sleep(
                ERROR_RETRY_SECONDS
            )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("========================================")
    print("          CHATBRAIN STARTING")
    print("========================================")
    print()

    # -----------------------------------------
    # Check client secret
    # -----------------------------------------

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

    # -----------------------------------------
    # YouTube login
    # -----------------------------------------

    try:

        youtube = get_youtube()

        print(
            "YouTube OAuth: CONNECTED"
        )

    except Exception as error:

        print()
        print(
            "YouTube login error:"
        )

        print(error)

        print()

        return

    # -----------------------------------------
    # Find active live
    # -----------------------------------------

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

    # -----------------------------------------
    # Start ChatBrain
    # -----------------------------------------

    start_chat(
        youtube,
        live_chat_id
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
