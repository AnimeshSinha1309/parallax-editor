"""DSPy LM wrapper that calls the upstream LLM via the OpenAI client.

This custom LM simply forwards requests to the configured endpoint, strips the
``<answer>...</answer>`` envelope that the upstream service adds, and hands the
result back in a format that DSPy understands.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from litellm import acompletion, completion
from litellm.utils import ModelResponse

from dspy.clients.base_lm import BaseLM

_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.DOTALL | re.IGNORECASE)


def _strip_answer_tags(text: str) -> str:
    """Remove a single <answer>...</answer> envelope from ``text`` if present."""

    if not isinstance(text, str):
        return text

    match = _ANSWER_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


class CustomLLMRouterLM(BaseLM):
    """DSPy LM that forwards requests through the LLM Router service."""

    def __init__(
        self,
        *,
        api_base: str,
        api_key: str,
        model: str = "gpt-4.1",
        temperature: float = 0.0,
        max_tokens: int = 1000,
        cache: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialise the custom LM wrapper."""

        super().__init__(
            model=model,
            model_type="chat",
            temperature=temperature,
            max_tokens=max_tokens,
            cache=cache,
            **kwargs,
        )

        self.api_base = api_base
        self.api_key = api_key

    def _build_payload(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build the request payload expected by the LLM Router service."""

        if messages:
            api_messages = messages
        elif prompt:
            api_messages = [{"role": "user", "content": prompt}]
        else:
            raise ValueError("Either prompt or messages must be provided.")

        merged_kwargs = {**self.kwargs, **kwargs}

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            **merged_kwargs,
        }

        return payload

    async def aforward(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Async forward pass returning an OpenAI-compatible response."""

        payload = self._build_payload(prompt=prompt, messages=messages, **kwargs)

        response = await acompletion(
            model=payload.pop("model"),
            api_base=self.api_base,
            api_key=self.api_key,
            messages=payload.pop("messages"),
            **payload,
        )
        for choice in response.choices:
            content = choice.message.get("content")
            if isinstance(content, str):
                choice.message["content"] = _strip_answer_tags(content)

        return response

    def forward(
        self,
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Sync forward pass returning an OpenAI-compatible response."""

        payload = self._build_payload(prompt=prompt, messages=messages, **kwargs)
        response = completion(
            model=payload.pop("model"),
            api_base=self.api_base,
            api_key=self.api_key,
            messages=payload.pop("messages"),
            **payload,
        )

        for choice in response.choices:
            content = choice.message.get("content")
            if isinstance(content, str):
                choice.message["content"] = _strip_answer_tags(content)

        return response


__all__ = ["CustomLLMRouterLM"]

