# parallax-editor

A plan editor with LLM powered live suggestions, made with K2 think.

## Code Search SDK

This repository includes a lightweight Python SDK for code search using ripgrep, designed for Parallax's Context Agent.

### Features

- **Fast**: Built on ripgrep for instant code search
- **Simple**: Zero dependencies (stdlib only)
- **Async**: Non-blocking I/O for better performance
- **Extensible**: Abstract interface allows future backends

### Quick Start

```python
import asyncio
from fulfillers.codesearch import CodeSearch

async def main():
    search = CodeSearch()

    # Check if ripgrep is available
    if not await search.is_available():
        print("Install ripgrep: brew install ripgrep")
        return

    # Search for code patterns
    result = await search.search(
        query="def.*retry",
        directory="/path/to/codebase",
        max_results=10
    )

    if result.success:
        for match in result.matches:
            print(f"{match.file_path}:{match.line_number}")
            print(f"  {match.line_content}")

asyncio.run(main())
```

### Installation

```bash
# Install ripgrep (required)
brew install ripgrep  # macOS
# or
sudo apt install ripgrep  # Ubuntu

# Install the package
pip install -e .

# For development
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run validation script
python tests/validate.py
```

### Documentation

See [docs/code-search-sdk-plan.md](docs/code-search-sdk-plan.md) for detailed technical documentation.
