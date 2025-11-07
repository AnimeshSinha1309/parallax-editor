"""Integration checks for the shared LM service."""

from __future__ import annotations

import os
import time
from typing import Final

import pytest

from utils.lm_service import get_lm, reset_lm


# These thresholds can be tuned if the upstream service characteristics change.
LATENCY_BUDGET_SECONDS: Final[float] = float(os.getenv("K2_LATENCY_BUDGET", "15"))


@pytest.mark.integration
@pytest.mark.slow
def test_k2_lm_round_trip() -> None:
    """Ensure the configured LM can complete a simple prompt within budget."""

    if not (os.getenv("K2_API_KEY") or os.getenv("CEREBRAS_API_KEY")):
        pytest.skip("K2/Cerebras API key not provided in environment")

    reset_lm()
    lm = get_lm()
    if lm is None:
        pytest.skip("LM unavailable after initialization")

    messages = [
        {
            "role": "user",
            "content": "Respond with the single word OK if you received this.",
        }
    ]

    start = time.perf_counter()

    try:
        response = lm.forward(messages=messages)
    except Exception as exc:  # noqa: BLE001 - Surface network/auth issues clearly.
        pytest.skip(f"LM request failed: {exc!r}")

    latency = time.perf_counter() - start
    assert latency <= LATENCY_BUDGET_SECONDS, (
        f"Latency {latency:.2f}s exceeded budget of {LATENCY_BUDGET_SECONDS:.2f}s"
    )

    content = response.choices[0].message.content.strip()
    assert content, "LM returned empty content"

