"""
RipgrepContext class for managing search directories and files.
"""

import os
import subprocess
from pathlib import Path
from typing import Set, Optional, Union


class RipgrepContextError(Exception):
    """Exception raised when RipgrepContext encounters an error."""
    pass


class RipgrepContext:
    """
    Manages the set of directories and files to search within using ripgrep.

    The context can be populated by:
    1. Adding paths directly
    2. Finding the git repository containing a given path
    3. Auto-discovering the current git repository

    Examples:
        # Auto-discover current git repo
        context = RipgrepContext()

        # Add specific directory
        context = RipgrepContext()
        context.add_path("/path/to/search")

        # Add path and its git repo
        context = RipgrepContext()
        context.add_git_repo("/path/to/file/in/repo")
    """

    def __init__(self, auto_add_current_repo: bool = True):
        """
        Initialize a new RipgrepContext.

        Args:
            auto_add_current_repo: If True and no paths are added, automatically
                                  discover and add the current git repository.
                                  Defaults to True.
        """
        self._paths: Set[Path] = set()
        self._auto_add_current_repo = auto_add_current_repo
        self._initialized = False

    def add_path(self, path: Union[str, Path]) -> None:
        """
        Add a file or directory path to the search context.

        Args:
            path: Path to a file or directory to include in searches.

        Raises:
            RipgrepContextError: If the path does not exist.
        """
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            raise RipgrepContextError(f"Path does not exist: {path}")

        self._paths.add(path_obj)
        self._initialized = True

    def add_git_repo(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Find and add the git repository containing the given path.

        If no path is provided, uses the current working directory.

        Args:
            path: Path to a file or directory inside a git repository.
                 If None, uses the current working directory.

        Raises:
            RipgrepContextError: If no git repository is found.
        """
        if path is None:
            search_path = Path.cwd()
        else:
            search_path = Path(path).resolve()
            if not search_path.exists():
                raise RipgrepContextError(f"Path does not exist: {path}")

        # Find the git repository root
        repo_root = self._find_git_root(search_path)
        if repo_root is None:
            raise RipgrepContextError(
                f"No git repository found for path: {search_path}"
            )

        self._paths.add(repo_root)
        self._initialized = True

    def _find_git_root(self, path: Path) -> Optional[Path]:
        """
        Find the root directory of the git repository containing the given path.

        Args:
            path: Path to search from (file or directory).

        Returns:
            Path to the git repository root, or None if not found.
        """
        # Start from the file's parent directory if it's a file
        current = path if path.is_dir() else path.parent

        # Walk up the directory tree looking for .git
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return current
            current = current.parent

        # Also check the root directory
        if (current / ".git").exists():
            return current

        # Alternative: use git command to find repo root
        try:
            result = subprocess.run(
                ["git", "-C", str(path.parent if path.is_file() else path), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def get_paths(self) -> Set[Path]:
        """
        Get the set of paths in this context.

        If no paths have been explicitly added and auto_add_current_repo is True,
        automatically discovers and adds the current git repository.

        Returns:
            Set of Path objects representing directories and files to search.

        Raises:
            RipgrepContextError: If no paths are available and git repo discovery fails.
        """
        # Auto-add current repo if no paths were explicitly added
        if not self._initialized and self._auto_add_current_repo:
            self.add_git_repo()

        if not self._paths:
            raise RipgrepContextError(
                "No paths in context. Add paths using add_path() or add_git_repo()."
            )

        return self._paths.copy()

    def clear(self) -> None:
        """Clear all paths from the context."""
        self._paths.clear()
        self._initialized = False

    def __len__(self) -> int:
        """Return the number of paths in the context."""
        return len(self._paths)

    def __repr__(self) -> str:
        """Return a string representation of the context."""
        return f"RipgrepContext(paths={len(self._paths)})"

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if not self._paths:
            return "RipgrepContext(empty)"
        return f"RipgrepContext with {len(self._paths)} path(s):\n" + \
               "\n".join(f"  - {p}" for p in sorted(self._paths))
