"""
Parallax - A modern terminal-based text editor with AI assistance.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

__version__ = "0.1.0"
