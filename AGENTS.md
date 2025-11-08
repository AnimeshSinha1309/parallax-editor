# Agent Guidelines

## Python Execution

**Always use `uv run` to execute Python commands.**

When running Python scripts, tests, or any Python-related commands, use `uv run` instead of directly calling `python` or `python3`.

Examples:
- ✅ `uv run python -c "from signatures import RGQueryGenerator"`
- ✅ `uv run pytest tests/`
- ❌ `python -c "..."` (don't use)
- ❌ `python3 script.py` (don't use)

This ensures that commands run in the correct virtual environment with all dependencies properly configured.

