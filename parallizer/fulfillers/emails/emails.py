"""Emails fulfiller for searching mailbox data relevant to current plan."""

from parallizer.utils import get_lm
from parallizer.signatures.email_searcher_signature import EmailSearcher
from parallizer.fulfillers.base import Fulfiller
from shared.models import Card, CardType
from shared.context import GlobalPreferenceContext
from typing import List, Tuple, Optional
from abc import ABCMeta
from pathlib import Path
import dspy
import logging

logger = logging.getLogger("parallax.emails")


# Create a combined metaclass to resolve the conflict between ABCMeta and dspy.Module's metaclass
class CombinedMeta(ABCMeta, type(dspy.Module)):
    """Combined metaclass for classes that inherit from both ABC and dspy.Module."""
    pass


class EmailsFulfiller(Fulfiller, dspy.Module, metaclass=CombinedMeta):
    """
    Emails fulfiller that searches mailbox data for emails relevant to the current plan.

    Uses DSPy to:
    1. Load emails from a local mbox file
    2. Search for 1-2 emails contextually relevant to the current plan document
    3. Return relevant emails as EMAIL cards
    """

    def __init__(self, mbox_path: str = "emails_data_dump.mbox", **kwargs):
        """
        Initialize the Emails fulfiller with DSPy module setup.

        Args:
            mbox_path: Path to the mbox file (relative to current working directory)
        """
        super().__init__(**kwargs)
        logger.info("Initializing EmailsFulfiller")

        # Store mbox path (will be resolved relative to scope_root at runtime)
        self.mbox_filename = mbox_path
        self.mailbox_data: List[str] = []

        # Initialize DSPy predictor
        lm = get_lm()
        if lm is not None:
            logger.info("LM configured successfully for EmailsFulfiller")
        else:
            logger.warning("No LM available for EmailsFulfiller")

        self.predictor = dspy.Predict(EmailSearcher)

    def _load_mbox_file(self, scope_root: str) -> List[str]:
        """
        Load emails from simple text file.

        Args:
            scope_root: Root directory where email file should be located

        Returns:
            List of email strings (formatted as "To: X, Subject: Y")
        """
        email_file_path = Path(scope_root) / self.mbox_filename
        emails = []

        try:
            if not email_file_path.exists():
                logger.warning(f"Email file not found: {email_file_path}")
                return emails

            logger.info(f"Loading emails from: {email_file_path}")

            with open(email_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    # Parse format: to:address@example.com Title of the Email
                    if line.startswith('to:'):
                        # Remove 'to:' prefix
                        content = line[3:]

                        # Split on first space to separate email from subject
                        parts = content.split(' ', 1)
                        if len(parts) >= 2:
                            email_addr = parts[0]
                            subject = parts[1]
                        elif len(parts) == 1:
                            email_addr = parts[0]
                            subject = "No Subject"
                        else:
                            logger.warning(f"Skipping malformed line {line_num}: {line}")
                            continue

                        # Format email as string
                        email_str = f"To: {email_addr}\nSubject: {subject}"
                        emails.append(email_str)
                    else:
                        logger.warning(f"Skipping invalid line {line_num} (doesn't start with 'to:'): {line}")

            logger.info(f"Loaded {len(emails)} emails from file")

        except Exception as e:
            logger.error(f"Error loading email file: {e}", exc_info=True)

        return emails

    async def forward(
        self,
        document_text: str,
        cursor_position: Tuple[int, int],
        global_context: GlobalPreferenceContext,
        intent_label: Optional[str] = None,
        **kwargs
    ) -> List[Card]:
        """
        Forward pass for emails fulfiller - finds relevant emails for current plan.

        Args:
            document_text: The entire text content of the current document
            cursor_position: (line, column) position of the cursor
            global_context: Global preference context containing scope root and plan path
            intent_label: Optional LLM-generated intent or label describing the query
            **kwargs: Additional parameters

        Returns:
            List of Card objects with EMAIL type containing relevant emails
        """
        logger.info(f"EmailsFulfiller invoked at {cursor_position}, scope_root={global_context.scope_root}, plan_path={global_context.plan_path}")

        # Load mbox file if not already loaded or if scope changed
        if not self.mailbox_data:
            self.mailbox_data = self._load_mbox_file(global_context.scope_root)

        # If no emails available, return empty list
        if not self.mailbox_data:
            logger.warning("No emails available in mailbox")
            return []

        # Read plan file if available, otherwise use document text
        plan_content = ""
        if global_context.plan_path:
            try:
                plan_path = Path(global_context.plan_path)
                if plan_path.exists() and plan_path.is_file():
                    plan_content = plan_path.read_text()
                    logger.info(f"Read plan file: {global_context.plan_path} ({len(plan_content)} characters)")
                else:
                    logger.warning(f"Plan file not found: {global_context.plan_path}")
            except Exception as e:
                logger.error(f"Failed to read plan file: {e}")

        # If no plan content, use document text as fallback
        if not plan_content:
            plan_content = document_text
            logger.info("Using document text as plan content (no plan file provided)")

        # Invoke DSPy predictor to find relevant emails
        logger.info(f"Searching {len(self.mailbox_data)} emails for relevance to plan")
        try:
            result = self.predictor(
                mailbox_data=self.mailbox_data,
                current_plan_document=plan_content
            )
        except Exception as e:
            logger.error(f"Error running email search predictor: {e}", exc_info=True)
            return []

        # Convert relevant emails to EMAIL cards
        cards = []
        if result.relevant_emails:
            logger.info(f"Found {len(result.relevant_emails)} relevant emails")
            for i, email in enumerate(result.relevant_emails, 1):
                # Extract subject for header (if available)
                header = "Relevant Email"
                if "Subject:" in email:
                    try:
                        subject_line = [line for line in email.split('\n') if line.startswith('Subject:')][0]
                        subject = subject_line.replace('Subject:', '').strip()
                        header = f"Email: {subject}"
                    except Exception:
                        pass

                card = Card(
                    header=header,
                    text=email,
                    type=CardType.EMAIL,
                    metadata={
                        "source": "emails",
                        "email_number": i,
                        "plan_path": global_context.plan_path
                    }
                )
                cards.append(card)
        else:
            logger.info("No relevant emails identified")

        logger.info(f"Generated {len(cards)} email cards")
        return cards

    async def is_available(self) -> bool:
        """Check if emails fulfiller is available (requires LM)."""
        from parallizer.utils import get_lm
        available = get_lm() is not None
        logger.info(f"EmailsFulfiller availability check: {available}")
        return available
