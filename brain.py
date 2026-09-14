from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2",
    temperature=0
)

def generate_response(message):

    prompt = f"""
You are ChatBrain for a YouTube livestream.

Read the subscriber's message and give a short,
clear and natural response.

Subscriber message:
{message}

Reply:
"""

    response = llm.invoke(prompt)

    return response.content