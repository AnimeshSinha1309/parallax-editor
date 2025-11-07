# Code Search SDK - Technical Plan (Ripgrep-Focused)

## 1. Executive Summary

**Purpose:** A lightweight Python SDK for code search using ripgrep, designed for Parallax's Context Agent.

**Why Ripgrep-Only?**
Based on [HN discussion](https://news.ycombinator.com/item?id=39993976):
- Ripgrep "brute forces through hundreds of MBs" of code near-instantly
- Hound has scaling issues (55MB JSON responses, slow rendering)
- For single codebase search, ripgrep is sufficient
- Zero server setup = zero complexity

**Input:**
- `query: str` - Search pattern (regex)
- `directory: str` - Path to search within

**Output:** Structured list of code matches with filenames, line numbers, and snippets

**Implementation Time:** ~1.5 hours (vs 3.5 hours for multi-backend approach)

---

## 2. Architecture Overview

```
┌─────────────────────────────────────┐
│         Context Agent               │
│                                     │
│  "Find similar retry logic"        │
└────────────┬────────────────────────┘
             │
             │ query="retry", directory="/project"
             ▼
┌─────────────────────────────────────┐
│        CodeSearch                   │
│                                     │
│  Simple facade over ripgrep         │
└────────────┬────────────────────────┘
             │
             │ async subprocess call
             ▼
┌─────────────────────────────────────┐
│        ripgrep (rg)                 │
│                                     │
│  System binary, JSON output         │
└─────────────────────────────────────┘
```

**Design Philosophy:**
- **Simple:** One backend, one code path
- **Fast:** Async subprocess execution
- **Extensible:** Abstract interface allows future backends (Hound, semantic search, etc.)
- **Pragmatic:** Solve 95% of use cases with 20% of the complexity

---

## 3. SDK Interface Design

### 3.1 Core Data Structures

```python
from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod

@dataclass
class SearchMatch:
    """A single match from code search"""
    file_path: str          # Path to file (relative to search dir)
    line_number: int        # Line number (1-indexed)
    line_content: str       # The matching line content
    context_before: List[str] = field(default_factory=list)  # Lines before match
    context_after: List[str] = field(default_factory=list)   # Lines after match

    def __str__(self) -> str:
        """Format as file:line for display"""
        return f"{self.file_path}:{self.line_number}"

@dataclass
class SearchResult:
    """Complete search result"""
    matches: List[SearchMatch]
    total_matches: int
    query: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """True if search completed without errors"""
        return self.error is None
```

### 3.2 Abstract Backend Interface (Future-Proofing)

```python
class CodeSearchBackend(ABC):
    """
    Abstract base class for code search implementations.

    Currently only RipgrepSearch is implemented.
    Future: HoundSearch, SemanticSearch, etc.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        directory: str,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False
    ) -> SearchResult:
        """Execute search and return results"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this backend is available"""
        pass
```

### 3.3 Main API (Simple Facade)

```python
class CodeSearch:
    """
    Main SDK interface for code search.

    Currently wraps RipgrepSearch directly.
    Simple, no fallback logic needed.

    Usage:
        search = CodeSearch()
        result = await search.search("def.*retry", "/path/to/code")
        for match in result.matches:
            print(f"{match.file_path}:{match.line_number}")
    """

    def __init__(self):
        self.backend = RipgrepSearch()

    async def search(
        self,
        query: str,
        directory: str,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False
    ) -> SearchResult:
        """
        Search for code patterns.

        Args:
            query: Regex pattern to search for
            directory: Directory to search in
            max_results: Maximum matches to return (default 50)
            context_lines: Lines of context before/after match (default 2)
            case_sensitive: Whether search is case-sensitive (default False)

        Returns:
            SearchResult with matches and metadata

        Example:
            result = await search.search("def main", ".", max_results=10)
            if result.success:
                print(f"Found {result.total_matches} matches")
        """
        return await self.backend.search(
            query, directory, max_results,
            context_lines, case_sensitive
        )

    async def is_available(self) -> bool:
        """Check if ripgrep is installed"""
        return await self.backend.is_available()
```

---

## 4. Ripgrep JSON Format (Critical Reference)

### 4.1 Command Format

```bash
rg --json -n -C 2 "pattern" /path/to/search
```

**Flags:**
- `--json`: Output newline-delimited JSON (NDJSON)
- `-n`: Show line numbers
- `-C 2`: Show 2 lines of context before/after matches
- Optional: `-i` for case-insensitive, `--max-count N` to limit results

### 4.2 Output Format

**Important:** Ripgrep outputs NDJSON (newline-delimited JSON). Each line is a separate JSON object.

```json
{"type":"begin","data":{"path":{"text":"src/retry.py"}}}
{"type":"match","data":{
  "path":{"text":"src/retry.py"},
  "lines":{"text":"def retry_request(url, max_attempts=3):\n"},
  "line_number":42,
  "absolute_offset":1234,
  "submatches":[{"match":{"text":"retry"},"start":4,"end":9}]
}}
{"type":"context","data":{
  "path":{"text":"src/retry.py"},
  "lines":{"text":"    for attempt in range(max_attempts):\n"},
  "line_number":43,
  "submatches":[]
}}
{"type":"end","data":{"path":{"text":"src/retry.py"}}}
{"type":"summary","data":{
  "elapsed_total":{"secs":0,"nanos":45123456},
  "stats":{"searches":1,"searches_with_match":1}
}}
```

### 4.3 Object Types

| Type | Purpose | Key Fields |
|------|---------|------------|
| `begin` | Start of file's results | `data.path.text` |
| `match` | A matching line | `path.text`, `line_number`, `lines.text` |
| `context` | Context line (before/after) | Same as match |
| `end` | End of file's results | `data.path.text` |
| `summary` | Overall stats | `stats.searches_with_match` |

### 4.4 Parsing Strategy

```python
def parse_ripgrep_json(output: bytes) -> List[SearchMatch]:
    """
    Parse ripgrep's NDJSON output into SearchMatch objects.

    Strategy:
    1. Split by newline - each line is separate JSON
    2. Track current file and context as we parse
    3. For each "match" type, collect preceding context lines
    4. Group context with matches
    """
    matches = []
    current_file = None
    context_buffer = []

    for line in output.decode('utf-8').strip().split('\n'):
        if not line:
            continue

        obj = json.loads(line)
        obj_type = obj.get('type')

        if obj_type == 'begin':
            current_file = obj['data']['path']['text']
            context_buffer = []

        elif obj_type == 'match':
            data = obj['data']
            match = SearchMatch(
                file_path=data['path']['text'],
                line_number=data['line_number'],
                line_content=data['lines']['text'].rstrip('\n'),
                context_before=context_buffer.copy()
            )
            matches.append(match)
            context_buffer = []

        elif obj_type == 'context':
            # Buffer context lines for next match
            data = obj['data']
            context_buffer.append(data['lines']['text'].rstrip('\n'))

    return matches
```

---

## 5. RipgrepSearch Implementation

```python
import asyncio
import json
import os
from typing import List
from .base import CodeSearchBackend
from .models import SearchMatch, SearchResult


class RipgrepSearch(CodeSearchBackend):
    """
    Code search implementation using ripgrep.

    Ripgrep is a fast, regex-based code search tool that's
    perfect for searching local codebases.

    Requirements:
        - ripgrep must be installed (brew install ripgrep)
        - Must be in PATH
    """

    async def search(
        self,
        query: str,
        directory: str,
        max_results: int = 50,
        context_lines: int = 2,
        case_sensitive: bool = False
    ) -> SearchResult:
        """
        Execute search using ripgrep.

        Returns SearchResult with matches or error.
        """
        try:
            # Build ripgrep command
            cmd = self._build_command(
                query, directory, max_results,
                context_lines, case_sensitive
            )

            # Execute with timeout
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                proc.kill()
                return SearchResult(
                    matches=[],
                    total_matches=0,
                    query=query,
                    error="Search timeout (>10s)"
                )

            # Check for errors
            if proc.returncode not in (0, 1):
                # 0 = matches found, 1 = no matches (not an error)
                error_msg = stderr.decode('utf-8').strip()
                return SearchResult(
                    matches=[],
                    total_matches=0,
                    query=query,
                    error=f"ripgrep error: {error_msg}"
                )

            # Parse results
            matches = self._parse_json_output(stdout)

            return SearchResult(
                matches=matches,
                total_matches=len(matches),
                query=query
            )

        except Exception as e:
            return SearchResult(
                matches=[],
                total_matches=0,
                query=query,
                error=f"Search failed: {str(e)}"
            )

    def _build_command(
        self,
        query: str,
        directory: str,
        max_results: int,
        context_lines: int,
        case_sensitive: bool
    ) -> List[str]:
        """Build ripgrep command with appropriate flags"""
        cmd = [
            "rg",
            "--json",           # JSON output
            "-n",               # Line numbers
            f"-C{context_lines}",  # Context lines
            "--max-count", str(max_results),  # Limit results per file
        ]

        if not case_sensitive:
            cmd.append("-i")

        # Add query and directory
        cmd.extend([query, directory])

        return cmd

    def _parse_json_output(self, output: bytes) -> List[SearchMatch]:
        """
        Parse ripgrep's NDJSON output.

        CRITICAL: Each line is a separate JSON object.
        DO NOT try to parse the entire output as single JSON.
        """
        matches = []
        context_buffer = []

        for line in output.decode('utf-8').strip().split('\n'):
            if not line:
                continue

            try:
                obj = json.loads(line)
                obj_type = obj.get('type')

                if obj_type == 'match':
                    data = obj['data']
                    match = SearchMatch(
                        file_path=data['path']['text'],
                        line_number=data['line_number'],
                        line_content=data['lines']['text'].rstrip('\n'),
                        context_before=context_buffer.copy(),
                        context_after=[]  # Filled by subsequent context lines
                    )
                    matches.append(match)
                    context_buffer = []

                elif obj_type == 'context':
                    # Context line - buffer for next match or add to previous
                    data = obj['data']
                    context_line = data['lines']['text'].rstrip('\n')

                    if matches and len(matches[-1].context_after) < 2:
                        # Add to previous match's after context
                        matches[-1].context_after.append(context_line)
                    else:
                        # Buffer as before context for next match
                        context_buffer.append(context_line)

            except (json.JSONDecodeError, KeyError) as e:
                # Skip malformed lines
                continue

        return matches

    async def is_available(self) -> bool:
        """Check if ripgrep is installed and in PATH"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "rg", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except FileNotFoundError:
            return False
```

---

## 6. Environment Setup

### 6.1 Installing Ripgrep

**macOS:**
```bash
brew install ripgrep
```

**Ubuntu/Debian:**
```bash
sudo apt install ripgrep
```

**Arch Linux:**
```bash
sudo pacman -S ripgrep
```

**Windows:**
```bash
choco install ripgrep
# or
scoop install ripgrep
```

**Verify Installation:**
```bash
rg --version
# Should output: ripgrep 14.x.x
```

### 6.2 No Configuration Required

Unlike Hound, ripgrep requires zero configuration. Just install and go.

---

## 7. Usage Examples

### 7.1 Basic Usage

```python
import asyncio
from fulfillers.codesearch import CodeSearch

async def main():
    search = CodeSearch()

    # Check if ripgrep is available
    if not await search.is_available():
        print("Error: ripgrep not installed")
        print("Install: brew install ripgrep")
        return

    # Simple search
    result = await search.search(
        query="def.*retry",
        directory="/path/to/codebase",
        max_results=10
    )

    if result.success:
        print(f"Found {result.total_matches} matches")
        for match in result.matches:
            print(f"\n{match.file_path}:{match.line_number}")
            print(f"  {match.line_content}")

            if match.context_before:
                print(f"  Before: {match.context_before}")
    else:
        print(f"Search failed: {result.error}")

asyncio.run(main())
```

### 7.2 Context Agent Integration

```python
class ContextAgent:
    """Agent that finds similar code in the codebase"""

    def __init__(self):
        self.code_search = CodeSearch()

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Extract key terms from markdown and find similar code.

        Args:
            context: Contains file_content, cursor_position, pwd

        Returns:
            AgentResponse with code references
        """
        # Extract search terms from the current section
        terms = self._extract_key_terms(context.file_content)

        if not terms:
            return AgentResponse(
                type="context",
                title="Similar Code",
                content="(no keywords found)"
            )

        # Build regex query (OR search)
        query = "|".join(terms)

        # Search codebase
        result = await self.code_search.search(
            query=query,
            directory=context.pwd,
            max_results=5,
            context_lines=1
        )

        if not result.success:
            return AgentResponse(
                type="context",
                title="Similar Code",
                content="(search unavailable)"
            )

        # Format for sidebar display
        if result.matches:
            content = "\n".join([
                str(match) for match in result.matches
            ])
        else:
            content = "(no matches found)"

        return AgentResponse(
            type="context",
            title="Similar Code",
            content=content
        )

    def _extract_key_terms(self, markdown: str) -> List[str]:
        """Extract function names, classes, key terms from markdown"""
        # Simple extraction - can be improved with NLP
        terms = []

        # Extract code blocks
        import re
        code_blocks = re.findall(r'`([^`]+)`', markdown)

        # Look for function-like patterns
        for block in code_blocks:
            if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', block):
                terms.append(block)

        return terms[:5]  # Top 5 terms
```

### 7.3 Advanced: Filtering by File Type

```python
# Search only Python files
result = await search.search(
    query="class.*Config",
    directory=".",
    max_results=20
)

# Filter results to only .py files
python_matches = [
    m for m in result.matches
    if m.file_path.endswith('.py')
]
```

---

## 8. Testing Strategy

### 8.1 Test Fixtures

Create `tests/fixtures/` with sample code:

**tests/fixtures/sample_code.py:**
```python
import sys

def retry_request(url, max_attempts=3):
    """Retry a request up to max_attempts times"""
    for attempt in range(max_attempts):
        try:
            return fetch(url)
        except RequestError:
            if attempt == max_attempts - 1:
                raise
    return None

class RetryHandler:
    def __init__(self, max_retries=5):
        self.max_retries = max_retries
```

**tests/fixtures/sample_code.js:**
```javascript
function retryFetch(url, maxAttempts = 3) {
    for (let i = 0; i < maxAttempts; i++) {
        try {
            return fetch(url);
        } catch (error) {
            if (i === maxAttempts - 1) throw error;
        }
    }
}
```

### 8.2 Unit Tests

```python
import pytest
from fulfillers.codesearch import CodeSearch, RipgrepSearch
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.mark.asyncio
async def test_ripgrep_available():
    """Test that ripgrep is installed"""
    rg = RipgrepSearch()
    assert await rg.is_available(), "ripgrep not installed"


@pytest.mark.asyncio
async def test_basic_search():
    """Test basic search functionality"""
    search = CodeSearch()

    result = await search.search(
        query="retry",
        directory=FIXTURES_DIR,
        max_results=10
    )

    assert result.success, f"Search failed: {result.error}"
    assert result.total_matches > 0, "No matches found"
    assert result.query == "retry"

    # Check match structure
    match = result.matches[0]
    assert hasattr(match, 'file_path')
    assert hasattr(match, 'line_number')
    assert hasattr(match, 'line_content')
    assert 'retry' in match.line_content.lower()


@pytest.mark.asyncio
async def test_case_sensitive():
    """Test case-sensitive search"""
    search = CodeSearch()

    # Case-insensitive (default)
    result_insensitive = await search.search(
        query="RETRY",
        directory=FIXTURES_DIR,
        case_sensitive=False
    )

    # Case-sensitive
    result_sensitive = await search.search(
        query="RETRY",
        directory=FIXTURES_DIR,
        case_sensitive=True
    )

    # Insensitive should find matches, sensitive should not
    assert result_insensitive.total_matches > 0
    assert result_sensitive.total_matches == 0


@pytest.mark.asyncio
async def test_context_lines():
    """Test that context lines are captured"""
    search = CodeSearch()

    result = await search.search(
        query="def retry_request",
        directory=FIXTURES_DIR,
        context_lines=2
    )

    assert result.success
    assert len(result.matches) > 0

    match = result.matches[0]
    # Should have context lines
    assert len(match.context_before) > 0 or len(match.context_after) > 0


@pytest.mark.asyncio
async def test_max_results():
    """Test that max_results is respected"""
    search = CodeSearch()

    result = await search.search(
        query="[a-z]+",  # Match any word
        directory=FIXTURES_DIR,
        max_results=3
    )

    assert result.success
    # Note: max_results is per-file in ripgrep
    # Total might be more, but should be limited


@pytest.mark.asyncio
async def test_nonexistent_directory():
    """Test search in nonexistent directory"""
    search = CodeSearch()

    result = await search.search(
        query="test",
        directory="/nonexistent/path/12345"
    )

    # Should return error, not crash
    assert not result.success
    assert result.error is not None


@pytest.mark.asyncio
async def test_invalid_regex():
    """Test search with invalid regex"""
    search = CodeSearch()

    result = await search.search(
        query="[invalid(",
        directory=FIXTURES_DIR
    )

    # Should handle gracefully
    assert not result.success
    assert result.error is not None
```

### 8.3 Integration Test

```python
@pytest.mark.asyncio
async def test_context_agent_integration():
    """Test integration with Context Agent"""
    from context_agent import ContextAgent, AgentContext

    agent = ContextAgent()

    # Simulate agent context
    context = AgentContext(
        file_content="""
        # Payment Retry Logic

        We need to implement retry logic for failed payment attempts.
        Use exponential backoff with max 3 retries.
        """,
        cursor_position=(5, 0),
        pwd=FIXTURES_DIR
    )

    response = await agent.process(context)

    assert response.type == "context"
    assert response.title == "Similar Code"
    assert "retry" in response.content.lower()
```

---

## 9. Project Structure

```
parallax-editor/
├── fulfillers/
│   └── codesearch/
│       ├── __init__.py         # Exports: CodeSearch, SearchResult, SearchMatch
│       ├── models.py           # SearchMatch, SearchResult dataclasses
│       ├── base.py             # CodeSearchBackend ABC
│       ├── ripgrep.py          # RipgrepSearch implementation
│       └── search.py           # CodeSearch facade
├── tests/
│   ├── fixtures/
│   │   ├── sample_code.py
│   │   └── sample_code.js
│   └── test_code_search.py    # All tests
├── docs/
│   └── code-search-sdk-plan.md  # This file
└── pyproject.toml
```

---

## 10. Dependencies

```toml
# pyproject.toml
[project]
name = "parallax-code-search"
version = "0.1.0"
description = "Lightweight code search SDK using ripgrep"
requires-python = ">=3.10"
dependencies = [
    # No dependencies! stdlib only
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

**External Requirements:**
- Python 3.10+
- `ripgrep` (system binary)

**No pip dependencies needed!** Uses only stdlib (`asyncio`, `json`, `dataclasses`).

---

## 11. Implementation Phases

### Phase 1: Core Structure (20 min)

**Tasks:**
- [ ] Create `fulfillers/codesearch/` directory
- [ ] Implement `models.py` with `SearchMatch` and `SearchResult`
- [ ] Implement `base.py` with `CodeSearchBackend` ABC
- [ ] Set up `pyproject.toml`
- [ ] Create `__init__.py` with exports

**Validation:**
```python
from fulfillers.codesearch import SearchMatch, SearchResult
match = SearchMatch("test.py", 42, "def test():")
assert str(match) == "test.py:42"
```

---

### Phase 2: Ripgrep Backend (40 min)

**Tasks:**
- [ ] Implement `ripgrep.py` with `RipgrepSearch` class
- [ ] Implement `_build_command()` method
- [ ] Implement `_parse_json_output()` method (CRITICAL - see Section 4.4)
- [ ] Implement `search()` with error handling
- [ ] Implement `is_available()` check

**Validation:**
```bash
# Test ripgrep directly first
rg --json -n "def" ./tests/fixtures/ | head -20

# Then test your code
python -c "
import asyncio
from fulfillers.codesearch.ripgrep import RipgrepSearch

async def test():
    rg = RipgrepSearch()
    print('Available:', await rg.is_available())
    result = await rg.search('def', './tests/fixtures')
    print(f'Matches: {result.total_matches}')

asyncio.run(test())
"
```

---

### Phase 3: Main API (10 min)

**Tasks:**
- [ ] Implement `search.py` with `CodeSearch` facade
- [ ] Wire up to `RipgrepSearch`
- [ ] Add docstrings and type hints

**Validation:**
```python
from fulfillers.codesearch import CodeSearch
import asyncio

async def test():
    search = CodeSearch()
    result = await search.search("test", ".")
    print(f"Found {result.total_matches} matches")

asyncio.run(test())
```

---

### Phase 4: Testing (30 min)

**Tasks:**
- [ ] Create `tests/fixtures/` with sample files
- [ ] Write unit tests (see Section 8.2)
- [ ] Run tests: `pytest tests/ -v`
- [ ] Fix any issues

**Validation:**
```bash
pytest tests/ -v --tb=short
# All tests should pass
```

---

**Total Implementation Time: ~1.5 hours**

---

## 12. Implementation Gotchas & Tips

### 12.1 CRITICAL: NDJSON Parsing

```python
# ❌ WRONG - will fail
output = '{"type":"match",...}\n{"type":"context",...}'
data = json.loads(output)  # JSONDecodeError!

# ✅ CORRECT - parse line by line
for line in output.split('\n'):
    if line:
        obj = json.loads(line)  # Parse each line separately
```

### 12.2 Async Subprocess

```python
# ❌ WRONG - blocks event loop
import subprocess
result = subprocess.run(["rg", ...])

# ✅ CORRECT - non-blocking
proc = await asyncio.create_subprocess_exec(
    "rg", ...,
    stdout=asyncio.subprocess.PIPE
)
stdout, stderr = await proc.communicate()
```

### 12.3 Ripgrep Exit Codes

```python
# Exit code 0: Matches found
# Exit code 1: No matches (NOT an error!)
# Exit code 2+: Actual error

if proc.returncode not in (0, 1):
    # Only treat 2+ as errors
    return error_result
```

### 12.4 Context Line Grouping

Context lines in ripgrep output are interleaved with matches. You need to track state:

```python
# Strategy:
# 1. Buffer context lines before a match
# 2. When match found, assign buffered lines as context_before
# 3. Subsequent context lines go to context_after
# 4. Reset buffer for next match
```

### 12.5 Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: rg` | ripgrep not installed | `brew install ripgrep` |
| `json.JSONDecodeError` | Parsing entire output as JSON | Parse line-by-line |
| Empty results | Wrong directory or no matches | Check directory exists |
| Timeout | Large codebase | Increase timeout or reduce max_results |

---

## 13. Edge Cases & Error Handling

### 13.1 No Ripgrep Installed

```python
search = CodeSearch()
if not await search.is_available():
    # Handle gracefully in agent
    return AgentResponse(
        type="context",
        title="Similar Code",
        content="(ripgrep not installed)"
    )
```

### 13.2 Invalid Regex

User might pass invalid regex. Ripgrep will return error code 2:

```python
# Ripgrep handles this - returns error in stderr
# Our code wraps it in SearchResult.error
result = await search.search("[invalid(", ".")
assert not result.success
assert "error" in result.error.lower()
```

### 13.3 Binary Files

Ripgrep automatically skips binary files. No action needed.

### 13.4 Large Codebases

```python
# Use max_results and timeout
result = await search.search(
    query="common_term",
    directory="/huge/codebase",
    max_results=20  # Limit to first 20 matches
)
# Timeout is already set to 10s in implementation
```

### 13.5 Empty Context

Some matches might have no context (file starts/ends). This is normal:

```python
match = SearchMatch(
    file_path="test.py",
    line_number=1,  # First line
    line_content="#!/usr/bin/env python",
    context_before=[],  # No lines before
    context_after=["", "import sys"]
)
```

---

## 14. Future Enhancements

**When ripgrep isn't enough (unlikely for v1):**

### 14.1 Hound Backend (If Scale Demands It)

If you have 100+ repos or multi-GB codebases, add `HoundSearch` backend:

```python
class CodeSearch:
    def __init__(self, use_hound: bool = False):
        if use_hound:
            self.backend = HoundSearch()  # Future
        else:
            self.backend = RipgrepSearch()
```

See HN discussion: Most teams never need this.

### 14.2 Semantic Search

```python
class SemanticSearch(CodeSearchBackend):
    """Use embeddings for code similarity"""
    # Future: Use sentence-transformers + faiss
```

### 14.3 Result Ranking

```python
# Rank by relevance, file importance, recency
matches.sort(key=lambda m: calculate_score(m))
```

### 14.4 Caching

```python
# Cache frequent searches (if needed)
from functools import lru_cache

@lru_cache(maxsize=100)
async def search_cached(query, directory):
    # ...
```

---

## 15. Success Criteria

**MVP Must Have:**
- ✅ Ripgrep integration working
- ✅ Async API
- ✅ Clean error handling
- ✅ Context lines support
- ✅ <100ms search latency for typical codebases
- ✅ Zero setup (just install ripgrep)

**Validation Script:**

```python
import asyncio
from fulfillers.codesearch import CodeSearch

async def validate():
    search = CodeSearch()

    # Test 1: Is ripgrep available?
    assert await search.is_available(), "❌ ripgrep not installed"
    print("✅ ripgrep is available")

    # Test 2: Basic search works
    result = await search.search("def", "./tests/fixtures", max_results=5)
    assert result.success, f"❌ Search failed: {result.error}"
    print(f"✅ Search works: {result.total_matches} matches")

    # Test 3: Results have correct structure
    if result.matches:
        m = result.matches[0]
        assert m.file_path and m.line_number and m.line_content
        print(f"✅ Structure correct: {m}")

    # Test 4: Error handling works
    bad_result = await search.search("[invalid(", ".")
    assert not bad_result.success
    print(f"✅ Error handling works: {bad_result.error}")

    print("\n🎉 All validation passed!")

asyncio.run(validate())
```

---

## 16. Quick Start for Implementation

### Step-by-Step Checklist

**Setup (5 min):**
- [ ] Install ripgrep: `brew install ripgrep`
- [ ] Verify: `rg --version`
- [ ] Create project structure: `mkdir -p fulfillers/codesearch tests/fixtures`
- [ ] Create `pyproject.toml`

**Phase 1 - Models (20 min):**
- [ ] Create `fulfillers/codesearch/models.py`
- [ ] Define `SearchMatch` dataclass
- [ ] Define `SearchResult` dataclass
- [ ] Test: Import and create instances

**Phase 2 - Backend (40 min):**
- [ ] Create `fulfillers/codesearch/base.py` with ABC
- [ ] Create `fulfillers/codesearch/ripgrep.py`
- [ ] Implement `_build_command()`
- [ ] Implement `_parse_json_output()` - **Read Section 4.4 carefully!**
- [ ] Implement `search()` with error handling
- [ ] Implement `is_available()`
- [ ] Test manually: `rg --json -n "test" .`

**Phase 3 - Facade (10 min):**
- [ ] Create `fulfillers/codesearch/search.py`
- [ ] Implement `CodeSearch` wrapper
- [ ] Create `fulfillers/codesearch/__init__.py`
- [ ] Test: `from fulfillers.codesearch import CodeSearch`

**Phase 4 - Testing (30 min):**
- [ ] Create sample files in `tests/fixtures/`
- [ ] Write tests from Section 8.2
- [ ] Run: `pytest tests/ -v`
- [ ] Fix any failures

**Phase 5 - Integration (15 min):**
- [ ] Test with Context Agent
- [ ] Run validation script (Section 15)
- [ ] Celebrate! 🎉

---

## 17. Debugging Guide

### Quick Debug Commands

```bash
# 1. Verify ripgrep works
rg --version
rg "test" ./tests/fixtures/

# 2. Test JSON output
rg --json -n "test" ./tests/fixtures/ | jq

# 3. Test your code with verbose output
python -c "
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from fulfillers.codesearch import CodeSearch

async def test():
    search = CodeSearch()
    result = await search.search('test', './tests/fixtures')
    print(f'Matches: {result.total_matches}')
    for m in result.matches[:3]:
        print(f'  {m}')

asyncio.run(test())
"

# 4. Run tests with output
pytest tests/ -v -s
```

### Common Issues

**"FileNotFoundError: rg"**
```bash
# Solution:
brew install ripgrep
# Verify: which rg
```

**"JSONDecodeError"**
```python
# You're trying to parse entire output as one JSON
# Fix: Parse line by line (see Section 4.4)
```

**"No matches found"**
```bash
# Debug: Run ripgrep directly
rg --json -n "your_query" /your/directory

# Check:
# - Does directory exist?
# - Does it contain matching files?
# - Is regex valid?
```

**Tests hanging**
```python
# Timeout issue - check async/await usage
# Make sure you're using:
proc = await asyncio.create_subprocess_exec(...)
stdout, stderr = await proc.communicate()
# NOT subprocess.run()
```

---

**Document Version:** 2.0 (Ripgrep-Focused)
**Author:** Claude (with user guidance)
**Status:** Ready for Implementation
**Last Updated:** 2025-11-06
**Implementation Time:** ~1.5 hours
