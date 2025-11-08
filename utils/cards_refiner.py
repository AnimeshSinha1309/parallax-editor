"""
Wrapper for CardsRefiner signature to handle card refinement logic.

This module provides a class that wraps the CardsRefiner DSPy signature,
handling the conversion between Card objects and JSON format, and providing
a clean interface for refining cards in the feed handler.
"""

from __future__ import annotations

import json
import logging
from typing import List

import dspy

from fulfillers.models import Card, CardType
from signatures.cards_refiner_signature import CardsRefiner
from utils.lm_service import get_lm

logger = logging.getLogger("parallax.cards_refiner")


class CardsRefinerWrapper:
    """
    Wrapper for the CardsRefiner signature that handles card refinement.

    This class provides a clean interface for refining cards by merging
    existing and newly proposed cards, minimizing UI disruption while
    incorporating new information.
    """

    def __init__(self):
        """Initialize the CardsRefinerWrapper with the DSPy signature."""
        logger.info("Initializing CardsRefinerWrapper")
        self.lm = get_lm()
        if self.lm is None:
            logger.warning("No LM available, CardsRefinerWrapper will not function")
        else:
            logger.debug(f"LM initialized: {self.lm}")

    def _cards_to_json(self, cards: List[Card]) -> str:
        """
        Convert a list of Card objects to JSON string format.

        Args:
            cards: List of Card objects to convert

        Returns:
            JSON string representation of the cards
        """
        cards_data = [
            {
                "header": card.header,
                "text": card.text,
                "metadata": card.metadata
            }
            for card in cards
        ]
        return json.dumps(cards_data, indent=2)

    def _json_to_cards(self, json_str: str, default_type: CardType = CardType.CONTEXT) -> List[Card]:
        """
        Convert a JSON string to a list of Card objects.

        Args:
            json_str: JSON string representing cards
            default_type: Default CardType to use for cards

        Returns:
            List of Card objects
        """
        try:
            cards_data = json.loads(json_str)
            if not isinstance(cards_data, list):
                logger.error(f"Expected list in JSON, got {type(cards_data)}")
                return []

            cards = []
            for item in cards_data:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict item: {item}")
                    continue

                # Extract card type from metadata if available, otherwise use default
                card_type = default_type
                if "type" in item:
                    try:
                        card_type = CardType(item["type"])
                    except ValueError:
                        logger.warning(f"Invalid card type: {item['type']}, using default {default_type}")

                card = Card(
                    header=item.get("header", ""),
                    text=item.get("text", ""),
                    type=card_type,
                    metadata=item.get("metadata", {})
                )
                cards.append(card)

            logger.debug(f"Converted JSON to {len(cards)} Card objects")
            return cards
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}", exc_info=True)
            logger.debug(f"Problematic JSON: {json_str}")
            return []
        except Exception as e:
            logger.error(f"Error converting JSON to cards: {e}", exc_info=True)
            return []

    def refine_cards(self, existing_cards: List[Card], newly_proposed_cards: List[Card]) -> List[Card]:
        """
        Refine cards by merging existing and newly proposed cards.

        This method uses the CardsRefiner signature to intelligently merge
        existing cards with newly proposed cards, minimizing UI disruption
        while incorporating new information.

        Args:
            existing_cards: List of currently displayed cards
            newly_proposed_cards: List of newly proposed cards from fulfillers

        Returns:
            List of refined cards to display
        """
        logger.info(f"Refining cards: {len(existing_cards)} existing, {len(newly_proposed_cards)} newly proposed")

        # If no LM is available, fall back to simple append behavior
        if self.lm is None:
            logger.warning("No LM available, returning newly proposed cards only")
            return newly_proposed_cards

        # If there are no existing cards, just return the new ones
        if not existing_cards:
            logger.info("No existing cards, returning newly proposed cards")
            return newly_proposed_cards

        # If there are no new cards, keep existing ones
        if not newly_proposed_cards:
            logger.info("No newly proposed cards, keeping existing cards")
            return existing_cards

        try:
            # Convert cards to JSON format
            existing_json = self._cards_to_json(existing_cards)
            new_json = self._cards_to_json(newly_proposed_cards)

            logger.debug(f"Existing cards JSON: {existing_json[:200]}...")
            logger.debug(f"New cards JSON: {new_json[:200]}...")

            # Configure DSPy to use the LM
            with dspy.context(lm=self.lm):
                # Create and invoke the signature
                refiner = dspy.Predict(CardsRefiner)
                logger.debug("Invoking CardsRefiner signature")

                result = refiner(
                    existing_cards=existing_json,
                    newly_proposed_cards=new_json
                )

                logger.debug(f"CardsRefiner result: {result.refined_cards[:200]}...")

                # Convert the result back to Card objects
                # Preserve the card types from the newly proposed cards where possible
                refined_cards = self._json_to_cards(result.refined_cards)

                # Match card types based on headers - prefer new card types if headers match
                new_cards_by_header = {card.header: card.type for card in newly_proposed_cards}
                for card in refined_cards:
                    if card.header in new_cards_by_header:
                        card.type = new_cards_by_header[card.header]

                logger.info(f"Refinement complete: {len(refined_cards)} refined cards")
                return refined_cards

        except Exception as e:
            logger.error(f"Error during card refinement: {e}", exc_info=True)
            logger.warning("Falling back to newly proposed cards due to error")
            return newly_proposed_cards


__all__ = ["CardsRefinerWrapper"]
