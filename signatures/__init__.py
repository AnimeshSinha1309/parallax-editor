"""DSPy signature definitions for Parallax sub-agents.

This package contains strongly-typed prompt interfaces that define
how each agent in the Parallax architecture communicates with the
underlying language model. Refer to the project documentation for
context on expected agent behaviors.
"""

from .completions_singnature import InlineCompletion
from .query_generator import RGQueryGenerator
from .question_ambiguity_signature import QuestionAmbiguityIdentifier

__all__ = ["InlineCompletion", "RGQueryGenerator", "QuestionAmbiguityIdentifier"]

