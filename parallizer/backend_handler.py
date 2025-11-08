"""
Parallizer Backend Server - FastAPI backend for Parallax Editor

This module provides a FastAPI server that:
1. Registers and manages fulfillers (Completions, Ambiguities, WebContext, CodeSearch)
2. Maintains feed state per user_id
3. Handles HTTP requests on /fulfill endpoint
4. Returns card objects as JSON
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from shared.models import Card, CardType
from shared.context import GlobalPreferenceContext
from parallizer.fulfillers.base import Fulfiller
from parallizer.fulfillers.completions.completions import Completions
from parallizer.fulfillers.ambiguities.ambiguities import Ambiguities
from parallizer.fulfillers.web_context.web_context import WebContext
from parallizer.fulfillers.codesearch.search import CodeSearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("parallizer.backend")

# FastAPI app
app = FastAPI(title="Parallizer Backend", version="0.1.0")

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
user_feeds: Dict[str, List[Card]] = defaultdict(list)
MAX_CARDS_PER_TYPE = 3


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


def initialize_fulfillers():
    """Initialize and register all available fulfillers"""
    global fulfillers

    logger.info("Initializing fulfillers...")

    try:
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


def enforce_card_limits(cards: List[Card]) -> List[Card]:
    """
    Enforce maximum cards per type (max 3 per type).

    Args:
        cards: List of cards to filter

    Returns:
        Filtered list with at most MAX_CARDS_PER_TYPE per type
    """
    card_counts = defaultdict(int)
    filtered_cards = []

    for card in cards:
        if card_counts[card.type] < MAX_CARDS_PER_TYPE:
            filtered_cards.append(card)
            card_counts[card.type] += 1

    return filtered_cards


def update_user_feed(user_id: str, new_cards: List[Card]) -> List[Card]:
    """
    Update the feed for a specific user with new cards.
    Maintains max 3 cards per type, removing oldest cards when limit is exceeded.

    Args:
        user_id: User identifier
        new_cards: New cards to add to feed

    Returns:
        Updated list of cards for the user
    """
    # Get current feed
    current_feed = user_feeds[user_id]

    # Separate cards by type
    cards_by_type = defaultdict(list)
    for card in current_feed:
        cards_by_type[card.type].append(card)

    # Add new cards
    for card in new_cards:
        cards_by_type[card.type].append(card)

        # Keep only the most recent MAX_CARDS_PER_TYPE per type
        if len(cards_by_type[card.type]) > MAX_CARDS_PER_TYPE:
            cards_by_type[card.type] = cards_by_type[card.type][-MAX_CARDS_PER_TYPE:]

    # Flatten back to single list
    updated_feed = []
    for card_type in CardType:
        updated_feed.extend(cards_by_type[card_type])

    # Update global state
    user_feeds[user_id] = updated_feed

    return updated_feed


async def invoke_fulfillers(
    document_text: str,
    cursor_position: tuple,
    global_context: GlobalPreferenceContext
) -> List[Card]:
    """
    Invoke all registered fulfillers concurrently.

    Args:
        document_text: Full document text
        cursor_position: (line, col) tuple
        global_context: Global preference context

    Returns:
        Flattened list of all cards from all fulfillers
    """
    if not fulfillers:
        logger.warning("No fulfillers registered")
        return []

    logger.info(f"Invoking {len(fulfillers)} fulfillers...")

    # Create tasks for all fulfillers
    tasks = []
    for fulfiller in fulfillers:
        try:
            # Check if fulfiller is available
            if await fulfiller.is_available():
                task = fulfiller.forward(
                    document_text=document_text,
                    cursor_position=cursor_position,
                    global_context=global_context
                )
                tasks.append(task)
            else:
                logger.info(f"Fulfiller {fulfiller.__class__.__name__} is not available")
        except Exception as e:
            logger.error(f"Error checking availability for {fulfiller.__class__.__name__}: {e}")

    # Execute all tasks concurrently
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and handle exceptions
        all_cards = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Fulfiller task {i} failed: {result}", exc_info=result)
            elif isinstance(result, list):
                all_cards.extend(result)
                logger.info(f"Fulfiller task {i} returned {len(result)} cards")

        logger.info(f"Total cards generated: {len(all_cards)}")
        return all_cards

    except Exception as e:
        logger.error(f"Error executing fulfiller tasks: {e}", exc_info=True)
        return []


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup"""
    logger.info("Starting Parallizer backend server...")
    initialize_fulfillers()
    logger.info("Parallizer backend ready!")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Parallizer Backend",
        "status": "running",
        "fulfillers": len(fulfillers),
        "users": len(user_feeds)
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
        "active_users": len(user_feeds)
    }


@app.post("/fulfill", response_model=FulfillResponse)
async def fulfill(request: FulfillRequest):
    """
    Main fulfillment endpoint.

    Receives document text and cursor position, invokes all fulfillers,
    and returns a list of cards as JSON.
    """
    try:
        logger.info(f"Received fulfill request from user: {request.user_id}")

        # Convert request models to internal types
        cursor_position = (request.cursor_position[0], request.cursor_position[1])
        global_context = GlobalPreferenceContext(
            scope_root=request.global_context.scope_root,
            plan_path=request.global_context.plan_path
        )

        # Invoke fulfillers
        new_cards = await invoke_fulfillers(
            document_text=request.document_text,
            cursor_position=cursor_position,
            global_context=global_context
        )

        # Update user feed
        updated_feed = update_user_feed(request.user_id, new_cards)

        # Convert cards to response format
        card_responses = []
        for card in updated_feed:
            card_responses.append(CardResponse(
                header=card.header,
                text=card.text,
                type=card.type.value,
                metadata=card.metadata
            ))

        logger.info(f"Returning {len(card_responses)} cards to user {request.user_id}")

        return FulfillResponse(cards=card_responses)

    except Exception as e:
        logger.error(f"Error processing fulfill request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/user/{user_id}/feed")
async def clear_user_feed(user_id: str):
    """Clear the feed for a specific user"""
    if user_id in user_feeds:
        del user_feeds[user_id]
        logger.info(f"Cleared feed for user: {user_id}")
        return {"status": "success", "message": f"Feed cleared for user {user_id}"}
    else:
        return {"status": "not_found", "message": f"No feed found for user {user_id}"}


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
