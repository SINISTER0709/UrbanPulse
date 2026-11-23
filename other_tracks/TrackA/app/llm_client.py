from typing import Any
from openai import OpenAI
from app.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
    RAG_LLM_MODEL,
)


class LLMClient:
    """Reusable OpenAI-SDK client for local Ollama, Groq, or OpenRouter."""

    def __init__(
        self,
        base_url: str = LLM_BASE_URL,
        api_key: str = LLM_API_KEY,
        model: str = LLM_MODEL,
        timeout: float = LLM_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url
        self.default_model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 128,
        json_mode: bool = False,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return (content or "").strip()


# Track A default client (fine-tuned classifier)
shared_llm_client = LLMClient(model=LLM_MODEL)

# Track F RAG client (base instruct model on the same endpoint)
rag_llm_client = LLMClient(model=RAG_LLM_MODEL)