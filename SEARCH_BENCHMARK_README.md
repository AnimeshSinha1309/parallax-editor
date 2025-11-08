# Search API Benchmark: Google Gemini vs Perplexity

This directory contains implementations and benchmarks comparing two search APIs:
- **Google Gemini Flash 2.5** with Google Search grounding
- **Perplexity Search API**

## Files

### Core Implementations

- **`parallizer/utils/google_search.py`**: Google Gemini Flash 2.5 with Search grounding implementation
- **`parallizer/utils/perplexity.py`**: Perplexity Search API implementation (pre-existing)

Both implementations share the same interface for easy interchangeability.

### Benchmark Scripts

- **`benchmark_search.py`**: Comprehensive benchmark comparing both search APIs
- **`test_google_search.py`**: Simple test script for Google Search implementation

## Setup

### 1. Install Dependencies

```bash
pip install aiohttp pydantic
```

Or install from the project root:

```bash
pip install -e .
```

### 2. Set API Keys

Create a `.env` file in the project root or set environment variables:

```bash
export GOOGLE_API_KEY="your_google_api_key_here"
export PERPLEXITY_API_KEY="your_perplexity_api_key_here"
```

#### Getting API Keys

**Google API Key:**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click "Get API key" → "Create API key"
3. Copy the key (starts with `AIza...`)

**Perplexity API Key:**
1. Go to [perplexity.ai](https://www.perplexity.ai/)
2. Navigate to API settings
3. Generate a new API key

## Usage

### Quick Test

Test the Google Search implementation with a simple query:

```bash
python test_google_search.py
```

### Run Full Benchmark

Run the comprehensive benchmark comparing both search APIs:

```bash
python benchmark_search.py
```

The benchmark will:
- Test both APIs with 8 diverse queries covering different search types
- Measure latency, content quality, and citation accuracy
- Display detailed comparisons for each query
- Save results to a JSON file: `benchmark_results_YYYYMMDD_HHMMSS.json`

### Using in Your Code

Both implementations share the same interface, making them interchangeable:

```python
import asyncio
from parallizer.utils.google_search import GoogleSearch
from parallizer.utils.perplexity import PerplexitySearch

async def main():
    # Use Google Search
    google = GoogleSearch()
    result = await google.search("What is Python asyncio?")

    if result.success:
        print(result.content)
        print("Citations:", result.citations)

    await google.close()

    # Or use Perplexity (same interface!)
    perplexity = PerplexitySearch()
    result = await perplexity.search("What is Python asyncio?")

    if result.success:
        print(result.content)
        print("Citations:", result.citations)

    await perplexity.close()

asyncio.run(main())
```

### Parallel Searches

Both implementations support parallel execution:

```python
import asyncio
from parallizer.utils.google_search import GoogleSearch

async def parallel_search():
    searcher = GoogleSearch()

    # Run multiple searches in parallel
    results = await asyncio.gather(
        searcher.search("Python asyncio"),
        searcher.search("Python best practices"),
        searcher.search("Python performance tips")
    )

    for result in results:
        if result.success:
            print(f"\nQuery: {result.content[:100]}...")
            print(f"Citations: {len(result.citations)}")

    await searcher.close()

asyncio.run(parallel_search())
```

## SearchResponse Interface

Both implementations return a `SearchResponse` object with the following fields:

```python
@dataclass
class SearchResponse:
    success: bool              # Whether the search succeeded
    content: str              # The search result content with inline citations
    citations: List[str]      # List of citation URLs
    error: Optional[str]      # Error message if failed
    raw_response: Optional[Dict[str, Any]]  # Raw API response

    def to_citation_list(self) -> List[str]:
        """Convert to list of "citation: content" strings"""
```

## Implementation Details

### Google Search (Gemini Flash 2.5)

- **Model**: `gemini-2.5-flash` (default)
- **Endpoint**: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
- **Features**:
  - Google Search grounding via `tools: [{"google_search": {}}]`
  - Automatic citation extraction from grounding metadata
  - Inline Markdown citations: `[1](url), [2](url)`
  - Async/await support with configurable concurrency
  - Semaphore-based rate limiting

### Perplexity Search

- **Model**: `sonar` (default)
- **Endpoint**: `https://api.perplexity.ai/chat/completions`
- **Features**:
  - Built-in web search and summarization
  - Citation URLs in response
  - Multiple model options (sonar, sonar-pro, sonar-reasoning, etc.)
  - Async/await support with configurable concurrency
  - Semaphore-based rate limiting

## Benchmark Metrics

The benchmark compares:

1. **Success Rate**: Percentage of successful queries
2. **Latency**: Average response time per query
3. **Content Length**: Average response length
4. **Citations**: Number and quality of sources
5. **Query-by-Query Comparison**: Detailed side-by-side results

## Example Benchmark Output

```
================================================================================
SEARCH API BENCHMARK: Google Gemini vs Perplexity
================================================================================

Timestamp: 2025-01-15T10:30:00
Queries: 8

📡 Checking API availability...
  Google Gemini: ✅ Available
  Perplexity: ✅ Available

🚀 Running 8 queries on both services in parallel...

================================================================================
BENCHMARK RESULTS
================================================================================

📊 OVERALL STATISTICS

Google Gemini:
  Success rate: 8/8 (100.0%)
  Avg latency: 2.45s
  Avg content length: 542 chars
  Avg citations per query: 4.2
  Total citations: 34

Perplexity:
  Success rate: 8/8 (100.0%)
  Avg latency: 3.12s
  Avg content length: 487 chars
  Avg citations per query: 3.8
  Total citations: 30

[... detailed query-by-query comparison ...]
```

## Notes

- Both implementations handle network errors and timeouts gracefully
- Rate limiting is implemented via semaphores (default: 10 concurrent requests)
- Sessions are properly managed with async context managers
- All citations include full URLs for verification

## Troubleshooting

### "GOOGLE_API_KEY not found" error

Make sure you've set the environment variable or added it to your `.env` file.

### DNS/Network errors

If you see "Temporary failure in name resolution", check your network connection and DNS settings.

### Rate limiting

Both APIs have rate limits. The implementations include semaphores to prevent excessive concurrent requests. Adjust `max_concurrent` parameter if needed:

```python
searcher = GoogleSearch(max_concurrent=5)  # Reduce concurrent requests
```

## License

MIT
