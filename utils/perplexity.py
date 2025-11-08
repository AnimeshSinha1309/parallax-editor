"""Perplexity API utilities for web search."""

import os
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass


@dataclass
class SearchResponse:
    """Response from Perplexity search."""

    success: bool
    content: str
    citations: List[str]
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_citation_list(self) -> List[str]:
        """
        Serialize search response to a list of citation-content strings.

        Returns:
            List of strings in the format ["citation_1: content", "citation_2: content", ...]
            If no citations are available, returns a single-element list with just the content.
        """
        if not self.success:
            return []

        if not self.citations:
            # No citations, return content as-is
            return [self.content]

        # Format as citation_N: content
        result = []
        for i, citation in enumerate(self.citations, 1):
            result.append(f"{citation}: {self.content}")

        return result


class PerplexitySearch:
    """
    Perplexity API client for web searches.

    Uses Perplexity's chat completion API with web search capabilities
    to perform Google-like searches and get AI-summarized results.

    Requirements:
        - PERPLEXITY_API_KEY in .env file (loaded via parallax package)
        - requests library (already in dependencies)

    Usage:
        # Basic search
        searcher = PerplexitySearch()
        result = searcher.search("Python asyncio best practices")
        if result.success:
            print(result.content)
            print("Sources:", result.citations)

        # Custom model
        searcher = PerplexitySearch(model="sonar")
        result = searcher.search("latest Python features")
    """

    BASE_URL = "https://api.perplexity.ai"
    DEFAULT_MODEL = "sonar"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30
    ):
        """
        Initialize Perplexity search client.

        Args:
            api_key: Perplexity API key. If None, reads from PERPLEXITY_API_KEY env var.
            model: Model to use for search. Default is sonar.
                  Available models:
                  - sonar(fastest, cost-effective)
                  - sonar-pro
                  - sonar-reasoning
                  - sonar-reasoning-pro
                  - sonar-deep-research
            timeout: Request timeout in seconds (default 30)
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "PERPLEXITY_API_KEY not found. Set it in .env file or environment."
            )

        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def search(
        self,
        query: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform a web search using Perplexity API.

        Args:
            query: Search query or question
            max_tokens: Maximum tokens in response (default 1024)
            temperature: Response creativity 0-1 (default 0.2 for factual)
            system_prompt: Optional system prompt to customize behavior

        Returns:
            SearchResponse with results or error

        Examples:
            # Factual search
            result = searcher.search("What is the capital of France?")

            # Research query
            result = searcher.search(
                "Latest developments in quantum computing",
                max_tokens=2000,
                system_prompt="Provide a detailed technical summary"
            )
        """
        try:
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Add user query
            messages.append({
                "role": "user",
                "content": query
            })

            # Make API request
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "return_citations": True,
                    "return_images": False,
                },
                timeout=self.timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract content and citations
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])

            return SearchResponse(
                success=True,
                content=content,
                citations=citations,
                raw_response=data
            )

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"API error: {error_detail.get('error', {}).get('message', str(e))}"
                except:
                    pass
            return SearchResponse(
                success=False,
                content="",
                citations=[],
                error=error_msg
            )

        except requests.exceptions.Timeout:
            return SearchResponse(
                success=False,
                content="",
                citations=[],
                error=f"Request timeout (>{self.timeout}s)"
            )

        except Exception as e:
            return SearchResponse(
                success=False,
                content="",
                citations=[],
                error=f"Search failed: {str(e)}"
            )

    def is_available(self) -> bool:
        """
        Check if Perplexity API is available and credentials are valid.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try a minimal request
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
                timeout=5
            )
            return response.status_code in (200, 429)  # 429 = rate limited but valid
        except:
            return False
