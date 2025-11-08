# Backend API Testing Guide

This directory contains comprehensive tests for the Parallizer backend API with **real LLM calls** (not mocked) and performance benchmarks.

## Test Files

### 1. `test_backend_api.py`
Comprehensive API tests using FastAPI TestClient.

**Test Coverage:**
- Health check endpoints (`/`, `/health`)
- Main fulfill endpoint (`/fulfill`)
- User feed management (`/user/{user_id}/feed`)
- Card type validation and limits
- Error handling and edge cases
- Correctness validation for all card types
- Performance benchmarks

**Features:**
- ✓ Real LLM calls (NOT mocked)
- ✓ Response validation
- ✓ Timing measurements
- ✓ Multi-user scenarios
- ✓ Edge case testing

### 2. `benchmark_fulfillers.py`
Detailed performance benchmarking for individual fulfillers.

**Benchmarks:**
- Completions (inline code completion)
- Ambiguities (question detection)
- WebContext (web search)
- CodeSearch (ripgrep)

**Metrics:**
- Average, min, max response times
- Standard deviation
- Cards per request
- Error rates

### 3. `fixtures/test_document.md`
Sample markdown document for testing, designed to trigger all fulfiller types.

## Prerequisites

```bash
# Install backend dependencies
cd parallizer
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio httpx
```

## Configuration

Set up environment variables:

```bash
# Required for LLM calls
export K2_API_KEY=your_api_key_here

# Optional
export PERPLEXITY_API_KEY=your_perplexity_key
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/test_backend_api.py -v -s

# Show print statements (-s flag is important for seeing benchmark output)
pytest tests/test_backend_api.py -v -s --tb=short
```

### Run Specific Test Classes

```bash
# Health endpoints only
pytest tests/test_backend_api.py::TestHealthEndpoints -v -s

# Fulfill endpoint tests
pytest tests/test_backend_api.py::TestFulfillEndpoint -v -s

# Benchmarks only
pytest tests/test_backend_api.py::TestFulfillerBenchmarks -v -s

# Correctness validation
pytest tests/test_backend_api.py::TestCorrectnessValidation -v -s
```

### Run Individual Fulfiller Benchmarks

```bash
# Detailed benchmarking script
python tests/benchmark_fulfillers.py

# This will:
# - Test each fulfiller individually
# - Run 3 iterations per fulfiller
# - Display detailed timing and card output
# - Save results to benchmark_results.json
```

## Expected Output

### Successful Test Run

```
test_backend_api.py::TestHealthEndpoints::test_root_endpoint PASSED
✓ Root endpoint: {'service': 'Parallizer Backend', 'status': 'running', 'fulfillers': 4}

test_backend_api.py::TestFulfillEndpoint::test_fulfill_basic_request PASSED
✓ Basic fulfill request completed in 3.45s
  Returned 5 cards
  - COMPLETION: Completion
  - QUESTION: How should we handle...
  - CONTEXT: Web search results...
```

### Benchmark Output

```
==================================================================
BENCHMARK: Complete Fulfill Request (All Fulfillers)
==================================================================

Run 1:
  Time: 4.23s
  Cards returned: 6
    - completion: 1
    - question: 3
    - context: 2

Run 2:
  Time: 3.87s
  Cards returned: 7
    - completion: 1
    - question: 3
    - context: 3

----------------------------------------------------------------------
Statistics over 3 runs:
  Average: 4.05s
  Min: 3.87s
  Max: 4.23s
==================================================================
```

## Performance Expectations

Based on real-world testing with K2 Think API:

| Fulfiller | Expected Time | Expected Cards |
|-----------|--------------|----------------|
| Completions | 1-3s | 0-1 |
| Ambiguities | 2-5s | 0-3 |
| WebContext | 3-6s | 0-3 |
| CodeSearch | 0.5-2s | 0-3 |
| **Combined** | **4-8s** | **0-9** |

*Note: Times vary based on document complexity and LLM availability*

## Test Data

### Test Document Stats
- **File**: `fixtures/test_document.md`
- **Size**: ~900 characters
- **Sections**:
  - Introduction
  - Python code example (Fibonacci)
  - TODO list
  - Questions/Ambiguities
  - Next steps

This document is designed to trigger:
- **Completions**: Code completion in Python section
- **Ambiguities**: Questions section
- **WebContext**: Technical terms (Python, Fibonacci)
- **CodeSearch**: Function definitions

## Interpreting Results

### Success Criteria

✓ **All tests pass**: Status code 200 for valid requests
✓ **Cards returned**: At least some cards from fulfillers
✓ **Card structure valid**: All required fields present
✓ **Type limits enforced**: Max 3 cards per type
✓ **Response time**: < 10s for complete request
✓ **No crashes**: All edge cases handled gracefully

### Common Issues

❌ **LLM not available**: Check K2_API_KEY is set
❌ **Slow responses**: Normal for first request (cold start)
❌ **No completion cards**: Cursor position may not trigger completions
❌ **Test timeout**: Increase timeout or reduce num_runs

## Troubleshooting

### Tests are slow
- First run is always slower (LLM cold start)
- Subsequent runs use cache
- Reduce `num_runs` in benchmarks

### Connection errors
```bash
# Check if backend dependencies are installed
pip list | grep -E "fastapi|uvicorn|dspy"

# Verify K2 API key is set
echo $K2_API_KEY
```

### Import errors
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/home/user/parallax-editor:$PYTHONPATH

# Or run from project root
cd /home/user/parallax-editor
pytest tests/test_backend_api.py -v -s
```

## CI/CD Integration

For continuous integration:

```yaml
# Example GitHub Actions
- name: Run Backend Tests
  env:
    K2_API_KEY: ${{ secrets.K2_API_KEY }}
  run: |
    pip install -r parallizer/requirements.txt
    pytest tests/test_backend_api.py -v --tb=short
```

## Contributing

When adding new tests:

1. Follow existing test structure
2. Use descriptive test names
3. Include timing measurements for benchmarks
4. Validate both structure AND content
5. Test edge cases
6. Add documentation for new test files

## License

Same as main project
