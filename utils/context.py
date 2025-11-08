"""
GlobalPreferenceContext class for managing global application preferences.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GlobalPreferenceContext:
    """
    Global context information passed to all fulfillers.

    Contains application-wide preferences and paths that fulfillers may need
    to properly execute their tasks.

    Attributes:
        scope_root: Root directory path for the scope
        plan_path: Optional path to the markdown plan file being edited
    """

    scope_root: str
    plan_path: Optional[str] = None
