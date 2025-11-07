"""Ripgrep-based code search implementation."""

import asyncio
import json
from typing import List, Optional

from .base import CodeSearchBackend
from .models import SearchMatch, SearchResult
from .context import RipgrepContext


class RipgrepSearch(CodeSearchBackend):
    """
    Code search implementation using ripgrep.

    Ripgrep is a fast, regex-based code search tool that's
    perfect for searching local codebases.

    Requirements:
        - ripgrep must be installed (brew install ripgrep)
        - Must be in PATH
    """

    def __init__(self, context: Optional[RipgrepContext] = None):
        """
        Initialize RipgrepSearch with an optional context.

        Args:
            context: RipgrepContext defining which directories/files to search.
                    If None, a new context will be created when needed.
        """
        self.context = context

    async def search(
        self,
        query: str,
        directory: Optional[str] = None,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False,
    ) -> SearchResult:
        """
        Execute search using ripgrep.

        Args:
            query: Regex pattern to search for
            directory: Directory to search in. If None, uses paths from context.
            max_results: Maximum total matches to return (default 50)
            context_lines: Lines of context before/after match (default 2)
            case_sensitive: Whether search is case-sensitive (default False)

        Returns:
            SearchResult with matches or error.
        """
        try:
            # Determine search paths
            if directory is not None:
                # Use provided directory (backwards compatible)
                search_paths = [directory]
            else:
                # Use context paths
                if self.context is None:
                    self.context = RipgrepContext()
                try:
                    search_paths = [str(p) for p in self.context.get_paths()]
                except Exception as e:
                    return SearchResult(
                        matches=[],
                        total_matches=0,
                        query=query,
                        error=f"Context error: {str(e)}",
                    )

            # Build ripgrep command
            cmd = self._build_command(
                query, search_paths, max_results, context_lines, case_sensitive
            )

            # Execute with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=10.0
                )
            except asyncio.TimeoutError:
                proc.kill()
                return SearchResult(
                    matches=[], total_matches=0, query=query, error="Search timeout (>10s)"
                )

            # Check for errors
            if proc.returncode not in (0, 1):
                # 0 = matches found, 1 = no matches (not an error)
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                return SearchResult(
                    matches=[],
                    total_matches=0,
                    query=query,
                    error=f"ripgrep error: {error_msg}",
                )

            # Parse results
            matches = self._parse_json_output(stdout, context_lines)

            # Enforce global max_results limit (ripgrep's --max-count is per-file)
            matches = matches[:max_results]

            return SearchResult(
                matches=matches, total_matches=len(matches), query=query
            )

        except Exception as e:
            return SearchResult(
                matches=[],
                total_matches=0,
                query=query,
                error=f"Search failed: {str(e)}",
            )

    def _build_command(
        self,
        query: str,
        search_paths: List[str],
        max_results: int,
        context_lines: int,
        case_sensitive: bool,
    ) -> List[str]:
        """Build ripgrep command with appropriate flags."""
        cmd = [
            "rg",
            "--json",  # JSON output
            "-n",  # Line numbers
            f"-C{context_lines}",  # Context lines
            "--max-count",
            str(max_results * 2),  # Per-file limit (set higher, we enforce globally)
        ]

        if not case_sensitive:
            cmd.append("-i")

        # Add query
        cmd.append(query)

        # Add all search paths
        cmd.extend(search_paths)

        return cmd

    def _parse_json_output(
        self, output: bytes, context_lines: int
    ) -> List[SearchMatch]:
        """
        Parse ripgrep's NDJSON output.

        CRITICAL: Each line is a separate JSON object.
        DO NOT try to parse the entire output as single JSON.

        Args:
            output: Raw bytes from ripgrep stdout
            context_lines: Expected number of context lines (for proper grouping)

        Returns:
            List of SearchMatch objects
        """
        matches = []
        context_buffer = []

        for line in output.decode("utf-8", errors="replace").strip().split("\n"):
            if not line:
                continue

            try:
                obj = json.loads(line)
                obj_type = obj.get("type")

                if obj_type == "match":
                    data = obj["data"]
                    match = SearchMatch(
                        file_path=data["path"]["text"],
                        line_number=data["line_number"],
                        line_content=data["lines"]["text"].rstrip("\n"),
                        context_before=context_buffer.copy(),
                        context_after=[],  # Filled by subsequent context lines
                    )
                    matches.append(match)
                    context_buffer = []

                elif obj_type == "context":
                    # Context line - buffer for next match or add to previous
                    data = obj["data"]
                    context_line = data["lines"]["text"].rstrip("\n")

                    # If we have a previous match and its context_after isn't full, add there
                    if matches and len(matches[-1].context_after) < context_lines:
                        matches[-1].context_after.append(context_line)
                    else:
                        # Buffer as before context for next match
                        # Keep only last N lines to avoid unbounded growth
                        context_buffer.append(context_line)
                        if len(context_buffer) > context_lines:
                            context_buffer.pop(0)

            except (json.JSONDecodeError, KeyError):
                # Skip malformed lines
                continue

        return matches

    async def is_available(self) -> bool:
        """Check if ripgrep is installed and in PATH."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rg",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except FileNotFoundError:
            return False
