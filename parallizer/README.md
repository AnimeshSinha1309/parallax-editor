# Parallizer - Backend Server for Parallax Editor

Parallizer is the backend server for the Parallax Editor, providing AI-powered code completion, ambiguity detection, and contextual search capabilities.

## Architecture

The backend includes:
- **Fulfillers**: AI services for completions, ambiguities, web context, and code search
- **Signatures**: DSPy signatures for LLM prompts
- **Utils**: Shared utilities (LM service, ripgrep, perplexity, query cache)

## Installation

```bash
cd parallizer
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
# Server configuration
export PARALLIZER_PORT=8000  # Optional, defaults to 8000
export PARALLIZER_HOST=0.0.0.0  # Optional, defaults to 0.0.0.0

# LM API configuration
export K2_API_BASE=https://llm-api.k2think.ai/v1
export K2_MODEL=openai/MBZUAI-IFM/K2-Think
export K2_API_KEY=your_api_key

# Optional: Perplexity API for web search
export PERPLEXITY_API_KEY=your_perplexity_key
```

## Running the Server

```bash
python -m parallizer.backend_handler
```

Or with custom port:

```bash
PARALLIZER_PORT=9000 python -m parallizer.backend_handler
```

## API Endpoints

### POST /fulfill

Main endpoint for fulfillment requests.

**Request:**
```json
{
  "user_id": "user123",
  "document_text": "def hello():\n    print('Hello')",
  "cursor_position": [1, 4],
  "global_context": {
    "scope_root": "/path/to/project",
    "plan_path": "/path/to/plan.md"
  }
}
```

**Response:**
```json
{
  "cards": [
    {
      "header": "Completion",
      "text": "world",
      "type": "completion",
      "metadata": {"confidence": 0.95}
    }
  ]
}
```

### GET /health

Health check endpoint showing fulfiller status.

### GET /

Basic status endpoint.

### DELETE /user/{user_id}/feed

Clear feed for a specific user.

## User Sessions

The server maintains feed state per `user_id` with no authentication required. Each user can have:
- Up to 3 COMPLETION cards
- Up to 3 QUESTION cards
- Up to 3 CONTEXT cards

Older cards are automatically removed when limits are exceeded.

## Development

Run tests:
```bash
pytest
```

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m parallizer.backend_handler
```
