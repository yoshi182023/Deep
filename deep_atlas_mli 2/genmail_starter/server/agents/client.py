import os

from openai import OpenAI

_client: OpenAI | None = None

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


def chat_completion(messages: list[dict], model: str | None = None) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=messages,
        temperature=0.3,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned an empty response")
    return content
