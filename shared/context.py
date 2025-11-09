"""
GlobalPreferenceContext class for managing global application preferences.
"""

import hashlib
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


def generate_user_id(context: GlobalPreferenceContext) -> str:
    """
    Generate a unique user ID based on the scope_root and plan_path.

    This ensures that each unique combination of scope_root and plan_path
    gets its own cache, while the same combination always produces the same ID.

    Args:
        context: GlobalPreferenceContext containing scope_root and plan_path

    Returns:
        A unique user ID string based on the hash of scope_root and plan_path
    """
    # Combine scope_root and plan_path for hashing
    # Use empty string if plan_path is None
    plan_path = context.plan_path or ""
    combined = f"{context.scope_root}:{plan_path}"

    # Create a SHA256 hash and take first 16 characters for readability
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    hash_str = hash_obj.hexdigest()[:16]

    return f"user-{hash_str}"
