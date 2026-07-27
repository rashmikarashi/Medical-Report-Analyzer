"""
llm_client.py
-------------
Thin wrapper so the Streamlit app can call either OpenAI or Groq
through one unified function, without duplicating logic per-provider.

Both OpenAI's and Groq's official Python SDKs expose a chat.completions.create
interface, so a single function can serve both by swapping the client and model.
"""

from openai import OpenAI
from groq import Groq


OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]


def get_client(provider: str, api_key: str):
    """Return an initialized client for the chosen provider."""
    if provider == "OpenAI":
        return OpenAI(api_key=api_key)
    elif provider == "Groq":
        return Groq(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def chat_completion(
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1500,
) -> str:
    """
    Send a system + user prompt to the chosen provider/model and return
    the plain text response. Raises exceptions upward so the UI layer
    can show a friendly error message.
    """
    client = get_client(provider, api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
