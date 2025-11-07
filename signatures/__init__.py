"""DSPy signature definitions for Parallax sub-agents.

This package contains strongly-typed prompt interfaces that define
how each agent in the Parallax architecture communicates with the
underlying language model. Refer to the project documentation for
context on expected agent behaviors.
"""

from .completion import GenerateInlineCompletion

__all__ = ["GenerateInlineCompletion"]

