"""DSPy LM wrapper that calls the upstream LLM via the OpenAI client.

This custom LM simply forwards requests to the configured endpoint, strips the
``<answer>...</answer>`` envelope that the upstream service adds, and hands the
result back in a format that DSPy understands.
"""

from __future__ import annotations

import json
import re
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional

from litellm import acompletion, completion
from litellm.utils import ModelResponse

from dspy.clients.base_lm import BaseLM

LOG_DIR = Path(__file__).resolve().parents[1] / "llm_logs"
LOG_FILE = LOG_DIR / "llm_requests.log"

_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.DOTALL | re.IGNORECASE)


def _strip_answer_tags(text: str) -> str:
    """Remove a single <answer>...</answer> envelope from ``text`` if present."""

    if not isinstance(text, str):
        return text

    match = _ANSWER_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


def _current_timestamp() -> str:
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


def _usage_to_dict(usage: Any) -> Dict[str, Any]:
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    for attr in ("model_dump", "dict"):
        method = getattr(usage, attr, None)
        if callable(method):
            try:
                data = method()
            except TypeError:
                try:
                    data = method(exclude_none=True)  # type: ignore[call-arg]
                except Exception:
                    continue
            except Exception:
                continue
            if isinstance(data, dict):
                return data
    if hasattr(usage, "__dict__"):
        return {
            key: value
            for key, value in vars(usage).items()
            if not key.startswith("_")
        }
    return {}


def _extract_token_usage(response: ModelResponse) -> Dict[str, Optional[int]]:
    usage_dict = _usage_to_dict(getattr(response, "usage", None))
    return {
        "input_tokens": usage_dict.get("prompt_tokens") or usage_dict.get("input_tokens"),
        "output_tokens": usage_dict.get("completion_tokens") or usage_dict.get("output_tokens"),
        "total_tokens": usage_dict.get("total_tokens"),
    }


def _extract_return_code(response: ModelResponse) -> Optional[int]:
    for attr in ("status_code", "status"):
        if hasattr(response, attr):
            code = getattr(response, attr)
            if isinstance(code, int):
                return code
    hidden_params = getattr(response, "_hidden_params", None)
    if isinstance(hidden_params, dict):
        code = hidden_params.get("status_code") or hidden_params.get("status")
        if isinstance(code, int):
            return code
    return None


def _extract_error_code(error: BaseException) -> Optional[int]:
    for attr in ("status_code", "status", "code", "http_status", "response_status"):
        if hasattr(error, attr):
            value = getattr(error, attr)
            if isinstance(value, int):
                return value
    return None


def _safe_log_event(event: Dict[str, Any]) -> None:
    enriched_event = {"timestamp": _current_timestamp(), **event}
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(enriched_event, default=str))
            log_file.write("\n")
    except Exception:
        # Logging must never block execution
        return


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
        """Async forward pass returning an OpenAI-compatible response.
        
        This method uses LiteLLM's acompletion for async LLM calls, which is
        compatible with DSPy's async interface (e.g., predictor.acall()).
        
        Args:
            prompt: Optional text prompt (mutually exclusive with messages).
            messages: Optional list of message dicts with 'role' and 'content'.
            **kwargs: Additional parameters passed to the LLM (temperature, max_tokens, etc.).
            
        Returns:
            ModelResponse: OpenAI-compatible response object with choices.
        """

        payload = self._build_payload(prompt=prompt, messages=messages, **kwargs)

        # Extract model and messages before passing remaining kwargs
        model = payload.pop("model")
        api_messages = payload.pop("messages")

        start_time = perf_counter()
        try:
            response = await acompletion(
                model=model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=api_messages,
                **payload,
            )
        except Exception as exc:
            latency_seconds = perf_counter() - start_time
            _safe_log_event(
                {
                    "status": "error",
                    "method": "aforward",
                    "model": model,
                    "latency_seconds": latency_seconds,
                    "messages_count": len(api_messages),
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "return_code": _extract_error_code(exc),
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            raise

        latency_seconds = perf_counter() - start_time
        token_usage = _extract_token_usage(response)
        _safe_log_event(
            {
                "status": "success",
                "method": "aforward",
                "model": model,
                "latency_seconds": latency_seconds,
                "messages_count": len(api_messages),
                **token_usage,
                "return_code": _extract_return_code(response),
            }
        )

        # Strip <answer> tags from response content (if present)
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
        model = payload.pop("model")
        api_messages = payload.pop("messages")

        start_time = perf_counter()
        try:
            response = completion(
                model=model,
                api_base=self.api_base,
                api_key=self.api_key,
                messages=api_messages,
                **payload,
            )
        except Exception as exc:
            latency_seconds = perf_counter() - start_time
            _safe_log_event(
                {
                    "status": "error",
                    "method": "forward",
                    "model": model,
                    "latency_seconds": latency_seconds,
                    "messages_count": len(api_messages),
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "return_code": _extract_error_code(exc),
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            raise

        latency_seconds = perf_counter() - start_time
        token_usage = _extract_token_usage(response)
        _safe_log_event(
            {
                "status": "success",
                "method": "forward",
                "model": model,
                "latency_seconds": latency_seconds,
                "messages_count": len(api_messages),
                **token_usage,
                "return_code": _extract_return_code(response),
            }
        )

        for choice in response.choices:
            content = choice.message.get("content")
            if isinstance(content, str):
                choice.message["content"] = _strip_answer_tags(content)

        return response


__all__ = ["CustomLLMRouterLM"]

