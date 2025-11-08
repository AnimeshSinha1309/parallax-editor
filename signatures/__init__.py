"""DSPy signature definitions for Parallax sub-agents.

This package contains strongly-typed prompt interfaces that define
how each agent in the Parallax architecture communicates with the
underlying language model. Refer to the project documentation for
context on expected agent behaviors.
"""

from .completions_signature import InlineCompletion
from .codebase_summary_signature import CodebaseSummary
from .query_generator import RGQueryGenerator
from .query_generator import create_cached_predictor as create_cached_rg_predictor
from .cards_refiner_signature import CardsRefiner
from .web_query_generator import WebQueryGenerator
from .web_query_generator import create_cached_predictor as create_cached_web_predictor

__all__ = [
    "InlineCompletion",
    "CodebaseSummary",
    "RGQueryGenerator",
    "create_cached_rg_predictor",
    "CardsRefiner",
    "WebQueryGenerator",
    "create_cached_web_predictor",
]

