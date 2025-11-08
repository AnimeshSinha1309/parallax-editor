"""
Parallizer Backend Server - FastAPI backend for Parallax Editor

This module provides a FastAPI server that:
1. Registers and manages fulfillers (Completions, Ambiguities, WebContext, CodeSearch)
2. Maintains feed state per user_id with incremental caching
3. Handles HTTP requests on /fulfill endpoint with background processing
4. Provides /cached endpoint for polling cached results
5. Returns card objects as JSON
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import dspy

from shared.models import Card, CardType
from shared.context import GlobalPreferenceContext
from parallizer.fulfillers.base import Fulfiller
from parallizer.fulfillers.completions.completions import Completions
from parallizer.fulfillers.ambiguities.ambiguities import Ambiguities
from parallizer.fulfillers.web_context.web_context import WebContext
from parallizer.fulfillers.codesearch.search import CodeSearch
from parallizer.utils import get_lm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("parallizer.backend")

# Configure DSPy at module level (before any async contexts)
# This ensures the LM is available in all async tasks
_lm = get_lm()
if _lm:
    dspy.configure(lm=_lm)
    logger.info("DSPy configured at module level")
else:
    logger.warning("No LM available at module level - fulfillers requiring LM may not work")

# FastAPI app
app = FastAPI(title="Parallizer Backend", version="0.2.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
fulfillers: List[Fulfiller] = []
MAX_CARDS_PER_TYPE = 3


@dataclass
class UserCache:
    """Cache structure for user feed state"""
    user_id: str
    cards: List[Card] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)
    processing: bool = False
    request_count: int = 0


# User caches with automatic cleanup
user_caches: Dict[str, UserCache] = {}
CACHE_EXPIRY_SECONDS = 3600  # 1 hour


# Pydantic models for request/response
class GlobalPreferenceContextModel(BaseModel):
    """Request model for global context"""
    scope_root: str
    plan_path: Optional[str] = None


class FulfillRequest(BaseModel):
    """Request model for /fulfill endpoint"""
    user_id: str
    document_text: str
    cursor_position: List[int]  # [line, col]
    global_context: GlobalPreferenceContextModel


class CardResponse(BaseModel):
    """Response model for Card"""
    header: str
    text: str
    type: str  # "question", "context", or "completion"
    metadata: Dict


class FulfillResponse(BaseModel):
    """Response model for /fulfill endpoint"""
    cards: List[CardResponse]
    processing: bool = False


class CachedResponse(BaseModel):
    """Response model for /cached endpoint"""
    cards: List[CardResponse]
    last_updated: float
    processing: bool


def initialize_fulfillers():
    """Initialize and register all available fulfillers"""
    global fulfillers

    logger.info("Initializing fulfillers...")

    try:
        # DSPy is already configured at module level, so we can proceed directly
        # to initializing fulfillers

        # Initialize each fulfiller
        completions = Completions()
        logger.info("Completions fulfiller initialized")

        ambiguities = Ambiguities()
        logger.info("Ambiguities fulfiller initialized")

        web_context = WebContext()
        logger.info("WebContext fulfiller initialized")

        code_search = CodeSearch()
        logger.info("CodeSearch fulfiller initialized")

        # Register all fulfillers
        fulfillers = [completions, ambiguities, web_context, code_search]

        logger.info(f"Successfully initialized {len(fulfillers)} fulfillers")

    except Exception as e:
        logger.error(f"Error initializing fulfillers: {e}", exc_info=True)
        # Continue with empty fulfillers list


def get_or_create_cache(user_id: str) -> UserCache:
    """Get or create user cache"""
    if user_id not in user_caches:
        user_caches[user_id] = UserCache(user_id=user_id)
        logger.info(f"Created new cache for user: {user_id}")
    return user_caches[user_id]


def update_user_cache_with_cards(user_id: str, new_cards: List[Card]) -> List[Card]:
    """
    Update user cache with new cards incrementally.
    Maintains max 3 cards per type, removing oldest cards when limit is exceeded.

    Args:
        user_id: User identifier
        new_cards: New cards to add to cache

    Returns:
        Updated list of cards for the user
    """
    cache = get_or_create_cache(user_id)

    # Separate cards by type
    cards_by_type = defaultdict(list)
    for card in cache.cards:
        cards_by_type[card.type].append(card)

    # Add new cards
    for card in new_cards:
        cards_by_type[card.type].append(card)

        # Keep only the most recent MAX_CARDS_PER_TYPE per type
        if len(cards_by_type[card.type]) > MAX_CARDS_PER_TYPE:
            cards_by_type[card.type] = cards_by_type[card.type][-MAX_CARDS_PER_TYPE:]
            logger.debug(f"Trimmed {card.type.value} cards to {MAX_CARDS_PER_TYPE} for user {user_id}")

    # Flatten back to single list
    updated_cards = []
    for card_type in CardType:
        updated_cards.extend(cards_by_type[card_type])

    # Update cache
    cache.cards = updated_cards
    cache.last_updated = time.time()

    logger.info(f"Updated cache for user {user_id}: {len(updated_cards)} total cards")

    return updated_cards


async def invoke_single_fulfiller(
    fulfiller: Fulfiller,
    user_id: str,
    document_text: str,
    cursor_position: tuple,
    global_context: GlobalPreferenceContext
):
    """
    Invoke a single fulfiller and update cache immediately with results.

    This allows incremental updates as each fulfiller completes.
    """
    fulfiller_name = fulfiller.__class__.__name__
    try:
        logger.info(f"[{user_id}] Starting fulfiller: {fulfiller_name}")
        start_time = time.time()

        # Check availability
        if not await fulfiller.is_available():
            logger.info(f"[{user_id}] Fulfiller {fulfiller_name} is not available")
            return

        # Execute fulfiller
        cards = await fulfiller.forward(
            document_text=document_text,
            cursor_position=cursor_position,
            global_context=global_context
        )

        elapsed = time.time() - start_time
        logger.info(f"[{user_id}] Fulfiller {fulfiller_name} completed in {elapsed:.2f}s with {len(cards)} cards")

        # Immediately update cache with these cards
        if cards:
            update_user_cache_with_cards(user_id, cards)
            logger.info(f"[{user_id}] Cache updated with {len(cards)} cards from {fulfiller_name}")

    except Exception as e:
        logger.error(f"[{user_id}] Fulfiller {fulfiller_name} failed: {e}", exc_info=True)


async def invoke_fulfillers_background(
    user_id: str,
    document_text: str,
    cursor_position: tuple,
    global_context: GlobalPreferenceContext
):
    """
    Invoke all fulfillers in parallel with incremental cache updates.
    This runs in the background and updates cache as each fulfiller completes.

    Args:
        user_id: User identifier
        document_text: Full document text
        cursor_position: (line, col) tuple
        global_context: Global preference context
    """
    if not fulfillers:
        logger.warning(f"[{user_id}] No fulfillers registered")
        return

    cache = get_or_create_cache(user_id)
    cache.processing = True
    cache.request_count += 1

    logger.info(f"[{user_id}] Starting background fulfiller execution ({len(fulfillers)} fulfillers)")

    try:
        # Create tasks for all fulfillers
        tasks = [
            invoke_single_fulfiller(
                fulfiller=fulfiller,
                user_id=user_id,
                document_text=document_text,
                cursor_position=cursor_position,
                global_context=global_context
            )
            for fulfiller in fulfillers
        ]

        # Execute all fulfillers in parallel
        # Each one will update cache independently as it completes
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"[{user_id}] All fulfillers completed")

    except Exception as e:
        logger.error(f"[{user_id}] Error in background fulfiller execution: {e}", exc_info=True)

    finally:
        cache.processing = False
        logger.info(f"[{user_id}] Background processing completed. Total cards in cache: {len(cache.cards)}")


def cleanup_old_caches():
    """Remove expired user caches"""
    current_time = time.time()
    expired_users = [
        user_id for user_id, cache in user_caches.items()
        if current_time - cache.last_updated > CACHE_EXPIRY_SECONDS
    ]

    for user_id in expired_users:
        del user_caches[user_id]
        logger.info(f"Cleaned up expired cache for user: {user_id}")

    if expired_users:
        logger.info(f"Cleaned up {len(expired_users)} expired caches")


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup"""
    logger.info("Starting Parallizer backend server...")
    initialize_fulfillers()
    logger.info("Parallizer backend ready!")


@app.get("/")
async def root():
    """Health check endpoint"""
    # Cleanup old caches periodically
    cleanup_old_caches()

    return {
        "service": "Parallizer Backend",
        "status": "running",
        "fulfillers": len(fulfillers),
        "active_users": len(user_caches)
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    fulfiller_status = []
    for fulfiller in fulfillers:
        try:
            available = await fulfiller.is_available()
            fulfiller_status.append({
                "name": fulfiller.__class__.__name__,
                "available": available
            })
        except Exception as e:
            fulfiller_status.append({
                "name": fulfiller.__class__.__name__,
                "available": False,
                "error": str(e)
            })

    return {
        "service": "Parallizer Backend",
        "status": "healthy",
        "fulfillers": fulfiller_status,
        "active_users": len(user_caches)
    }


@app.post("/fulfill", response_model=FulfillResponse)
async def fulfill(request: FulfillRequest, background_tasks: BackgroundTasks):
    """
    Main fulfillment endpoint with background processing.

    This endpoint triggers background fulfiller execution and immediately returns
    the current cached state. Fulfillers continue executing in the background and
    update the cache incrementally as they complete.

    The client can poll /cached to get updates as they become available.
    """
    try:
        logger.info(f"Received fulfill request from user: {request.user_id}")

        # Convert request models to internal types
        cursor_position = (request.cursor_position[0], request.cursor_position[1])
        global_context = GlobalPreferenceContext(
            scope_root=request.global_context.scope_root,
            plan_path=request.global_context.plan_path
        )

        # Get current cache
        cache = get_or_create_cache(request.user_id)

        # Trigger background processing
        background_tasks.add_task(
            invoke_fulfillers_background,
            user_id=request.user_id,
            document_text=request.document_text,
            cursor_position=cursor_position,
            global_context=global_context
        )

        logger.info(f"[{request.user_id}] Background processing triggered")

        # Return current cached cards immediately
        card_responses = []
        for card in cache.cards:
            card_responses.append(CardResponse(
                header=card.header,
                text=card.text,
                type=card.type.value,
                metadata=card.metadata
            ))

        logger.info(f"Returning {len(card_responses)} cached cards to user {request.user_id} (processing in background)")

        return FulfillResponse(
            cards=card_responses,
            processing=True
        )

    except Exception as e:
        logger.error(f"Error processing fulfill request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/cached/{user_id}", response_model=CachedResponse)
async def get_cached(user_id: str):
    """
    Get cached cards for a user without triggering new fulfiller execution.

    This endpoint is polled by the frontend to get incremental updates
    as fulfillers complete in the background.

    Returns:
        Current cached cards, last update timestamp, and processing status
    """
    try:
        logger.debug(f"Cached request from user: {user_id}")

        # Get cache (or create empty one if doesn't exist)
        cache = get_or_create_cache(user_id)

        # Convert cards to response format
        card_responses = []
        for card in cache.cards:
            card_responses.append(CardResponse(
                header=card.header,
                text=card.text,
                type=card.type.value,
                metadata=card.metadata
            ))

        logger.debug(f"Returning {len(card_responses)} cached cards for user {user_id} (processing={cache.processing})")

        return CachedResponse(
            cards=card_responses,
            last_updated=cache.last_updated,
            processing=cache.processing
        )

    except Exception as e:
        logger.error(f"Error getting cached data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/user/{user_id}/feed")
async def clear_user_feed(user_id: str):
    """Clear the cache for a specific user"""
    if user_id in user_caches:
        del user_caches[user_id]
        logger.info(f"Cleared cache for user: {user_id}")
        return {"status": "success", "message": f"Cache cleared for user {user_id}"}
    else:
        return {"status": "not_found", "message": f"No cache found for user {user_id}"}


def main():
    """Run the Parallizer backend server"""
    port = int(os.getenv("PARALLIZER_PORT", "8000"))
    host = os.getenv("PARALLIZER_HOST", "0.0.0.0")

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
