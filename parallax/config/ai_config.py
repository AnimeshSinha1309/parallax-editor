"""
Configuration for AI information feed.

This module defines the structure and content for AI information boxes
that appear in the right pane of the Parallax editor.
"""

# Configuration for AI feed information boxes
# Each box has a header and content
# Modify this list to customize the AI feed display
AI_FEED_CONFIG = [
    {
        "header": "Information",
        "content": (
            "This is a placeholder for AI-generated information about your code. "
            "When integrated with an AI endpoint, this section will display:\n\n"
            "• Code analysis\n"
            "• Suggestions for improvement\n"
            "• Documentation summaries\n"
            "• Context-aware insights"
        )
    },
    {
        "header": "References",
        "content": (
            "Placeholder for relevant references:\n\n"
            "• [Textual Documentation](https://textual.textualize.io/)\n"
            "• [Python Style Guide](https://peps.python.org/pep-0008/)\n"
            "• **Local files**: [ai_feed.py](./parallax/widgets/ai_feed.py)\n"
            "• [app.py at line 62](file:///home/user/parallax-editor/parallax/app.py:62)\n"
            "• *Example relative path*: [README.md](./README.md)"
        )
    },
    {
        "header": "Suggestions",
        "content": (
            "AI will provide code suggestions here:\n\n"
            "• Refactoring opportunities\n"
            "• Performance optimizations\n"
            "• Security improvements\n"
            "• Code style recommendations\n"
            "• Alternative approaches"
        )
    },
    {
        "header": "Errors & Warnings",
        "content": (
            "Real-time error and warning detection:\n\n"
            "• Syntax errors\n"
            "• Type mismatches\n"
            "• Potential bugs\n"
            "• Code smells\n"
            "• Deprecated usage"
        )
    },
]


def get_ai_feed_config() -> list[dict[str, str]]:
    """
    Get the current AI feed configuration.

    Returns:
        list: List of dictionaries containing 'header' and 'content' keys
    """
    return AI_FEED_CONFIG


def update_ai_feed_config(new_config: list[dict[str, str]]):
    """
    Update the AI feed configuration.

    Args:
        new_config: New configuration list with 'header' and 'content' dicts
    """
    global AI_FEED_CONFIG
    AI_FEED_CONFIG = new_config


def add_info_box(header: str, content: str):
    """
    Add a new information box to the AI feed.

    Args:
        header: The header text for the box
        content: The content text for the box
    """
    AI_FEED_CONFIG.append({
        "header": header,
        "content": content
    })
