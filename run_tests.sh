#!/bin/bash
# Test runner script for Parallizer backend API tests

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Parallizer Backend Test Runner${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

# Check if K2_API_KEY is set
if [ -z "$K2_API_KEY" ]; then
    echo -e "${YELLOW}Warning: K2_API_KEY not set${NC}"
    echo "LLM-based tests may fail. Set with:"
    echo "  export K2_API_KEY=your_api_key_here"
    echo ""
fi

# Check dependencies
echo -e "${GREEN}Checking dependencies...${NC}"
cd "$PROJECT_ROOT/parallizer"
pip install -q -r requirements.txt 2>/dev/null || true

cd "$PROJECT_ROOT"

# Parse command line arguments
TEST_TYPE="${1:-all}"

case "$TEST_TYPE" in
    "health")
        echo -e "${GREEN}Running health endpoint tests...${NC}"
        pytest tests/test_backend_api.py::TestHealthEndpoints -v -s
        ;;
    "fulfill")
        echo -e "${GREEN}Running fulfill endpoint tests...${NC}"
        pytest tests/test_backend_api.py::TestFulfillEndpoint -v -s
        ;;
    "benchmark")
        echo -e "${GREEN}Running benchmark tests...${NC}"
        pytest tests/test_backend_api.py::TestFulfillerBenchmarks -v -s
        ;;
    "correctness")
        echo -e "${GREEN}Running correctness validation tests...${NC}"
        pytest tests/test_backend_api.py::TestCorrectnessValidation -v -s
        ;;
    "edge")
        echo -e "${GREEN}Running edge case tests...${NC}"
        pytest tests/test_backend_api.py::TestEdgeCases -v -s
        ;;
    "fulfillers")
        echo -e "${GREEN}Running individual fulfiller benchmarks...${NC}"
        python tests/benchmark_fulfillers.py
        ;;
    "quick")
        echo -e "${GREEN}Running quick test suite (no benchmarks)...${NC}"
        pytest tests/test_backend_api.py::TestHealthEndpoints -v -s
        pytest tests/test_backend_api.py::TestFulfillEndpoint::test_fulfill_basic_request -v -s
        ;;
    "all"|*)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest tests/test_backend_api.py -v -s
        ;;
esac

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Tests completed!${NC}"
echo -e "${GREEN}================================${NC}"
