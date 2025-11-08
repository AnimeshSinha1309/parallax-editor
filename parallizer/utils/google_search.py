"""Google Gemini API with Google Search grounding for web search with async support."""

import os
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
from dataclasses import dataclass


@dataclass
class SearchResponse:
    """Response from Google Search (matches Perplexity interface)."""

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


class GoogleSearch:
    """
    Async Google Gemini API client with Google Search grounding.

    Uses Gemini 2.5 Flash with Google Search tool integration to perform
    web searches and get AI-summarized results with citations.

    Now supports async/await for parallel execution with asyncio.gather().

    Requirements:
        - GOOGLE_API_KEY in .env file or environment
        - aiohttp library for async HTTP

    Usage:
        # Basic search
        searcher = GoogleSearch()
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

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = 30,
        max_concurrent: int = 10
    ):
        """
        Initialize Google Search client.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            model: Model to use for search. Default is gemini-2.5-flash.
                  Available models:
                  - gemini-2.5-flash (recommended for search)
                  - gemini-2.5-pro
            timeout: Request timeout in seconds (default 30)
            max_concurrent: Maximum concurrent requests (default 10)
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in .env file or environment."
            )

        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        # Semaphore to limit concurrent requests (prevent rate limiting)
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Shared session (will be created on first use)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _add_citations_to_text(
        self,
        text: str,
        grounding_metadata: Optional[Dict[str, Any]]
    ) -> tuple[str, List[str]]:
        """
        Add inline citations to text based on grounding metadata.

        Args:
            text: The original text from the response
            grounding_metadata: Grounding metadata from the response

        Returns:
            Tuple of (text_with_citations, list_of_citation_urls)
        """
        if not grounding_metadata:
            return text, []

        supports = grounding_metadata.get("groundingSupports", [])
        chunks = grounding_metadata.get("groundingChunks", [])

        if not supports or not chunks:
            return text, []

        # Sort supports by end_index in reverse to insert citations from end to start
        sorted_supports = sorted(
            supports,
            key=lambda s: s.get("segment", {}).get("endIndex", 0),
            reverse=True
        )

        # Track unique citation URLs
        citation_urls = []
        citation_map = {}  # URL -> citation number

        # Process each support to add inline citations
        for support in sorted_supports:
            segment = support.get("segment", {})
            end_index = segment.get("endIndex", 0)
            chunk_indices = support.get("groundingChunkIndices", [])

            if chunk_indices:
                citation_links = []
                for idx in chunk_indices:
                    if idx < len(chunks):
                        chunk = chunks[idx]
                        web = chunk.get("web", {})
                        uri = web.get("uri", "")

                        if uri:
                            # Get or create citation number
                            if uri not in citation_map:
                                citation_map[uri] = len(citation_urls) + 1
                                citation_urls.append(uri)

                            citation_num = citation_map[uri]
                            citation_links.append(f"[{citation_num}]({uri})")

                if citation_links:
                    citation_string = ", ".join(citation_links)
                    text = text[:end_index] + citation_string + text[end_index:]

        return text, citation_urls

    async def search(
        self,
        query: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None
    ) -> SearchResponse:
        """
        Perform an async web search using Google Gemini API with search grounding.

        Args:
            query: Search query or question
            max_tokens: Maximum tokens in response (default 1024)
            temperature: Response creativity 0-2 (default 0.2 for factual)
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
                # Build the request payload
                contents = []

                # Add system instruction if provided
                system_instruction = None
                if system_prompt:
                    system_instruction = {"parts": [{"text": system_prompt}]}

                # Add user query
                contents.append({
                    "parts": [{"text": query}]
                })

                payload = {
                    "contents": contents,
                    "tools": [{"google_search": {}}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    }
                }

                if system_instruction:
                    payload["system_instruction"] = system_instruction

                # Get session
                session = await self._get_session()

                # Make API request
                url = f"{self.BASE_URL}/{self.model}:generateContent"
                headers = {
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json"
                }

                async with session.post(
                    url,
                    json=payload,
                    headers=headers
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

                    # Extract content from response
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return SearchResponse(
                            success=False,
                            content="",
                            citations=[],
                            error="No response from API"
                        )

                    candidate = candidates[0]
                    content_parts = candidate.get("content", {}).get("parts", [])

                    # Concatenate all text parts
                    raw_text = ""
                    for part in content_parts:
                        if "text" in part:
                            raw_text += part["text"]

                    # Get grounding metadata
                    grounding_metadata = candidate.get("groundingMetadata")

                    # Add citations to text
                    content_with_citations, citation_urls = self._add_citations_to_text(
                        raw_text,
                        grounding_metadata
                    )

                    return SearchResponse(
                        success=True,
                        content=content_with_citations,
                        citations=citation_urls,
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
        Check if Google API is available and credentials are valid.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            session = await self._get_session()

            # Try a minimal request with short timeout
            url = f"{self.BASE_URL}/{self.model}:generateContent"
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            async with session.post(
                url,
                json={
                    "contents": [{"parts": [{"text": "test"}]}],
                    "generationConfig": {"maxOutputTokens": 1}
                },
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                # 200 = success, 429 = rate limited but valid credentials
                return response.status in (200, 429)
        except:
            return False

    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            # Schedule session close
            try:
                asyncio.get_event_loop().create_task(self.close())
            except:
                pass
