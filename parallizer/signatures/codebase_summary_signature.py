"""DSPy signature and predictor for summarizing scoped codebases and plans."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, Sequence

import dspy
from persist_cache.persist_cache import cache


class CodebaseSummary(dspy.Signature):
    """Summarize the intent and purpose of a scoped repository segment."""

    current_plan_document: str = dspy.InputField(
        desc=(
            "Latest high-level plan or task document describing the intended changes "
            "or goals for this scope. Include numbered steps, notes, and any context "
            "that clarifies what is being attempted."
        )
    )
    scope_tree_structure: str = dspy.InputField(
        desc=(
            "Textual tree representation of the repository or scoped directory. "
            "Include directory hierarchy and file names to expose overall structure "
            "and important entry points."
        )
    )
    scope_readme: str = dspy.InputField(
        desc=(
            "Contents of the README file located in the scoped directory, if present. "
            "Pass an empty string when no README exists."
        )
    )

    summary_markdown: str = dspy.OutputField(
        desc=(
            "Single markdown-formatted paragraph or list that concisely explains the "
            "primary intent of the scoped repository segment, how the current plan "
            "relates to that intent, and the overall purpose of the codebase."
        )
    )


class CodebaseSummaryPredictor(dspy.Module):
    """
    DSPy module that constructs CodebaseSummary inputs from filesystem paths.

    Args:
        plan_document_path: Path to the plan document file.
        scope_directory_path: Path to the repository or scoped directory root.
    """

    def __init__(
        self,
        *,
        max_tree_depth: int = 4,
        max_entries: int = 200,
        excluded_names: Sequence[str] | None = None,
    ) -> None:
        super().__init__()
        self.predictor = dspy.Predict(CodebaseSummary)
        self.max_tree_depth = max_tree_depth
        self.max_entries = max_entries
        self.excluded_names = set(excluded_names or [])

    def forward(self, plan_document_path: str, scope_directory_path: str):
        """
        Build CodebaseSummary inputs from disk and call the underlying predictor.
        """
        plan_text, tree, readme_text = self._prepare_inputs(plan_document_path, scope_directory_path)

        return self.predictor(
            current_plan_document=plan_text,
            scope_tree_structure=tree,
            scope_readme=readme_text,
        )

    async def aforward(self, plan_document_path: str, scope_directory_path: str):
        """
        Async counterpart leveraging DSPy's native async support via acall().
        """
        plan_text, tree, readme_text = await asyncio.to_thread(
            self._prepare_inputs, plan_document_path, scope_directory_path
        )

        return await self.predictor.acall(
            current_plan_document=plan_text,
            scope_tree_structure=tree,
            scope_readme=readme_text,
        )

    def _prepare_inputs(self, plan_document_path: str, scope_directory_path: str) -> tuple[str, str, str]:
        plan_path = Path(plan_document_path)
        scope_root = Path(scope_directory_path)
        plan_text = _read_text_file(plan_path)
        tree = _build_tree(scope_root, self.max_tree_depth, self.max_entries, self.excluded_names)
        readme_text = _read_readme(scope_root)
        return plan_text, tree, readme_text


def _summarize_codebase_impl(plan_document_path: str, scope_directory_path: str) -> str:
    predictor = CodebaseSummaryPredictor()
    result = predictor(
        plan_document_path=plan_document_path,
        scope_directory_path=scope_directory_path,
    )
    return getattr(result, "summary_markdown", "")


@cache(name="summarize_codebase", dir=".persist_cache/codebase_summary/sync")
def summarize_codebase(plan_document_path: str, scope_directory_path: str) -> str:
    """
    Summarize the codebase and plan documents using CodebaseSummaryPredictor.

    Results are cached on disk using persist-cache for fast repeated access.
    """
    return _summarize_codebase_impl(plan_document_path, scope_directory_path)


@cache(name="summarize_codebase_async", dir=".persist_cache/codebase_summary/async")
async def summarize_codebase_async(plan_document_path: str, scope_directory_path: str) -> str:
    """
    Async counterpart to summarize_codebase with persistent disk caching.
    """
    predictor = CodebaseSummaryPredictor()
    result = await predictor.acall(
        plan_document_path=plan_document_path,
        scope_directory_path=scope_directory_path,
    )
    return getattr(result, "summary_markdown", "")


def _read_text_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _build_tree(
    root: Path,
    max_depth: int,
    max_entries: int,
    excluded_names: Iterable[str],
) -> str:
    if not root.exists():
        return ""

    excluded = {name.lower() for name in excluded_names}
    lines: list[str] = []
    entries_count = 0

    def walk(current: Path, depth: int, prefix: str) -> None:
        nonlocal entries_count
        if depth > max_depth or entries_count >= max_entries:
            return

        children = sorted(
            (
                child
                for child in current.iterdir()
                if not child.name.startswith(".")
                and child.name.lower() not in excluded
            ),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )

        for index, child in enumerate(children):
            if entries_count >= max_entries:
                lines.append(f"{prefix}... (truncated)")
                return

            connector = "|-- "
            line = f"{prefix}{connector}{child.name}"
            if child.is_dir():
                line += "/"
            lines.append(line)
            entries_count += 1

            if child.is_dir():
                next_prefix = f"{prefix}|   "
                walk(child, depth + 1, next_prefix)

    root_name = root.name or str(root)
    lines.append(f"{root_name}/")
    if root.is_dir():
        walk(root, 1, "")

    return "\n".join(lines)


def _read_readme(scope_root: Path) -> str:
    if not scope_root.exists():
        return ""

    readme_candidates = [
        child
        for child in scope_root.iterdir()
        if child.is_file() and child.name.lower().startswith("readme")
    ]
    if not readme_candidates:
        return ""

    # Prefer markdown README files for richer context.
    readme_candidates.sort(
        key=lambda path: (
            path.suffix.lower() not in {".md", ".markdown"},
            path.name.lower(),
        )
    )

    return _read_text_file(readme_candidates[0])


__all__ = [
    "CodebaseSummary",
    "CodebaseSummaryPredictor",
    "summarize_codebase",
    "summarize_codebase_async",
]

