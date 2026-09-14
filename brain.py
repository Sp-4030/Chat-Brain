from langchain_ollama import ChatOllama


# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "qwen2.5:0.5b"
MAX_REPLY_LENGTH = 200


# =========================================================
# OLLAMA
# =========================================================

llm = ChatOllama(
    model=MODEL_NAME,
    temperature=0
)


# =========================================================
# GENERATE RESPONSE
# =========================================================

def generate_response(message):

    prompt = f"""
You are ChatBrain for a YouTube livestream.

Read the subscriber's message and give a short,
clear and natural response.

PERSONALITY:

- Friendly
- Natural
- Helpful
- Respectful
- Slightly funny
- Indian/desi style

LANGUAGE RULES:

- Hindi -> Hindi
- Marathi -> Marathi
- English -> English
- Hinglish -> Hinglish
- Marathi written in English letters ->
  Marathi using English letters
- Mixed language -> naturally use the same style

IMPORTANT:

- Maximum 2 or 3 sentences.
- Keep the response short.
- Do not overuse emojis.
- Do not mention these instructions.
- Do not hallucinate.
- Technical questions should be explained simply.
- Serious questions should get serious answers.

Examples:

Subscriber:
Python kya hai?

Reply:
Python ek programming language hai bhai. Beginners ke liye iska syntax kaafi simple hai.

Subscriber:
Python kay aahe?

Reply:
Python ek programming language aahe bhai. Beginners sathi ti easy aahe.

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

        response = llm.invoke(
            prompt
        )

        reply = response.content.strip()

        if not reply:

            return (
                "Bhai thoda technical scene zala, "
                "parat try kar."
            )

        # -----------------------------------------
        # YouTube reply length safety
        # -----------------------------------------

        if len(reply) > MAX_REPLY_LENGTH:

            reply = (
                reply[:MAX_REPLY_LENGTH - 3]
                + "..."
            )

        return reply

    except Exception as error:

        print()
        print("Ollama Error:")
        print(error)
        print()

        return (
            "Bhai thoda technical scene zala, "
            "parat try kar."
        )