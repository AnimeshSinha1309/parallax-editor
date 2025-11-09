"""Perplexity API utilities for web search with async support."""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger("parallax.perplexity")


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
    Async Perplexity API client for web searches.

    Uses Perplexity's chat completion API with web search capabilities
    to perform Google-like searches and get AI-summarized results.

    Now supports async/await for parallel execution with asyncio.gather().

    Requirements:
        - PERPLEXITY_API_KEY in .env file (loaded via parallax package)
        - aiohttp library for async HTTP

    Usage:
        # Basic search
        searcher = PerplexitySearch()
        result = await searcher.search("Python asyncio best practices")
        if result.success:
            print(result.content)
            print("Sources:", result.citations)

        # Parallel searches
        results = await asyncio.gather(
            searcher.search("Python asyncio"),
            searcher.search("Python performance"),
            searcher.search("Python best practices")
        )
    """

    BASE_URL = "https://api.perplexity.ai"
    DEFAULT_MODEL = "sonar"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30,
        max_concurrent: int = 10
    ):
        """
        Initialize Perplexity search client.

        Args:
            api_key: Perplexity API key. If None, reads from PERPLEXITY_API_KEY env var.
            model: Model to use for search. Default is sonar.
                  Available models:
                  - sonar (fastest, cost-effective)
                  - sonar-pro
                  - sonar-reasoning
                  - sonar-reasoning-pro
                  - sonar-deep-research
            timeout: Request timeout in seconds (default 30)
            max_concurrent: Maximum concurrent requests (default 10)
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "PERPLEXITY_API_KEY not found. Set it in .env file or environment."
            )

        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Semaphore to limit concurrent requests (prevent rate limiting)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Shared session (will be created on first use)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=self.timeout
            )
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def search(
        self,
        query: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform an async web search using Perplexity API.

        Args:
            query: Search query or question
            max_tokens: Maximum tokens in response (default 1024)
            temperature: Response creativity 0-1 (default 0.2 for factual)
            system_prompt: Optional system prompt to customize behavior

        Returns:
            SearchResponse with results or error

        Examples:
            # Single search
            result = await searcher.search("What is the capital of France?")

            # Parallel searches
            results = await asyncio.gather(
                searcher.search("Python basics"),
                searcher.search("Python advanced"),
                searcher.search("Python performance")
            )
        """
        # Use semaphore to limit concurrent requests
        async with self._semaphore:
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

                # Get session
                session = await self._get_session()

                # Make API request
                async with session.post(
                    f"{self.BASE_URL}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "return_citations": True,
                        "return_images": False,
                    }
                ) as response:
                    # Check for HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        try:
                            error_data = await response.json()
                            error_msg = f"API error: {error_data.get('error', {}).get('message', error_text)}"
                        except:
                            error_msg = f"HTTP {response.status}: {error_text}"

                        return SearchResponse(
                            success=False,
                            content="",
                            citations=[],
                            error=error_msg
                        )

                    # Parse response
                    data = await response.json()

                    # Extract content and citations
                    content = data["choices"][0]["message"]["content"]
                    citations = data.get("citations", [])

                    return SearchResponse(
                        success=True,
                        content=content,
                        citations=citations,
                        raw_response=data
                    )

            except asyncio.TimeoutError:
                return SearchResponse(
                    success=False,
                    content="",
                    citations=[],
                    error=f"Request timeout (>{self.timeout.total}s)"
                )

            except aiohttp.ClientError as e:
                return SearchResponse(
                    success=False,
                    content="",
                    citations=[],
                    error=f"HTTP error: {str(e)}"
                )

            except Exception as e:
                return SearchResponse(
                    success=False,
                    content="",
                    citations=[],
                    error=f"Search failed: {str(e)}"
                )

    async def is_available(self) -> bool:
        """
        Check if Perplexity API is available and credentials are valid.

        Returns:
            True if API key is present (even if network check fails)
        """
        # If no API key, definitely not available
        if not self.api_key:
            logger.warning("Perplexity API key not found")
            return False

        try:
            session = await self._get_session()

            # Try a minimal request with short timeout
            async with session.post(
                f"{self.BASE_URL}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                },
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                # 200 = success, 429 = rate limited but valid credentials
                return response.status in (200, 429)
        except asyncio.TimeoutError:
            logger.warning("Perplexity API timeout during availability check - assuming available (network issue)")
            return True  # Return True anyway - likely network/firewall issue
        except aiohttp.ServerDisconnectedError:
            logger.warning("Perplexity API server disconnected during availability check - assuming available (network/firewall issue)")
            return True  # Return True anyway - network is blocking connection
        except aiohttp.ClientError as e:
            logger.warning(f"Perplexity API connection error: {type(e).__name__}: {e} - assuming available")
            return True  # Return True anyway - likely network/firewall issue
        except Exception as e:
            logger.error(f"Perplexity API availability check failed: {type(e).__name__}: {e}")
            return False

    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            # Schedule session close
            try:
                asyncio.get_event_loop().create_task(self.close())
            except:
                pass
