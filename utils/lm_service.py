"""Shared LM initialization utilities for the K2 Think deployment.

This module provides a single, stateful `dspy.LM` instance configured to talk to
the K2 Think API. The LM is lazily instantiated and cached so it can be safely
reused across the codebase without reinitializing the underlying client.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import dspy
from dotenv import load_dotenv

# Load environment variables (e.g., during local development or CLI usage).
load_dotenv()

# Default endpoint/model can still be overridden via environment variables.
LM_API_BASE = os.getenv(
    "K2_API_BASE",
    os.getenv("CEREBRAS_API_BASE", "https://llm-api.k2think.ai/v1"),
)
LM_MODEL = os.getenv(
    "K2_MODEL",
    os.getenv("CEREBRAS_MODEL", "openai/MBZUAI-IFM/K2-Think"),
)

_global_lm: Optional[dspy.LM] = None
_global_lm_lock = threading.Lock()


def get_lm(
    api_key: Optional[str] = None,
    *,
    force_refresh: bool = False,
) -> Optional[dspy.LM]:
    """Return a shared Cerebras-backed `dspy.LM` instance.

    Args:
        api_key: Optional override for the Cerebras API key.
        force_refresh: If True, rebuild the cached LM even if one already exists.

    Returns:
        A singleton `dspy.LM` instance or ``None`` if no API key is available.
    """

    resolved_api_key = api_key or os.getenv("K2_API_KEY")
    if not resolved_api_key:
        return None

    global _global_lm
    with _global_lm_lock:
        if _global_lm is not None and not force_refresh:
            return _global_lm

        _global_lm = dspy.LM(
            model=LM_MODEL,
            api_key=resolved_api_key,
            api_base=LM_API_BASE,
            max_tokens=1000,
            temperature=0.7,
        )

        return _global_lm


def reset_lm() -> None:
    """Clear the cached LM instance (primarily for tests)."""

    global _global_lm
    with _global_lm_lock:
        _global_lm = None


__all__ = [
    "LM_API_BASE",
    "LM_MODEL",
    "get_lm",
    "reset_lm",
]


