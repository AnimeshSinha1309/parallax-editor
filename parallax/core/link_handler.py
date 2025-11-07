"""
Link handler utilities for the AI feed.

Handles different types of links:
- file:/// links (absolute file paths)
- Relative file paths
- http/https URLs
- Line number support for file links
"""

import os
import subprocess
import re
from pathlib import Path
from urllib.parse import urlparse


class LinkHandler:
    """Handles different types of links from the AI feed."""

    def __init__(self, root_path: str = None):
        """
        Initialize the link handler.

        Args:
            root_path: The root path for resolving relative file paths
        """
        self.root_path = root_path or os.getcwd()

    def handle_link(self, href: str) -> tuple[bool, str]:
        """
        Handle a link click and perform the appropriate action.

        Args:
            href: The link href to handle

        Returns:
            tuple: (success: bool, message: str)
        """
        # Parse the link type
        parsed = urlparse(href)

        if parsed.scheme in ('http', 'https'):
            return self._open_web_link(href)
        elif parsed.scheme == 'file':
            # Extract path from file:// URL
            file_path = parsed.path
            return self._open_file_link(file_path)
        else:
            # Assume it's a relative or absolute file path
            return self._open_file_link(href)

    def _open_web_link(self, url: str) -> tuple[bool, str]:
        """
        Open a web link in the default browser.

        Args:
            url: The URL to open

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Use xdg-open on Linux, open on macOS, start on Windows
            if os.name == 'posix':
                if os.uname().sysname == 'Darwin':
                    subprocess.Popen(['open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(['start', url], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return (True, f"Opening {url} in browser")
        except Exception as e:
            return (False, f"Failed to open URL: {str(e)}")

    def _open_file_link(self, file_path: str) -> tuple[bool, str]:
        """
        Open a file link in neovim using tmux.

        Supports line numbers in the format: path/to/file:42

        Args:
            file_path: The file path to open (may include :line_number)

        Returns:
            tuple: (success: bool, message: str)
        """
        # Parse line number if present
        line_number = None
        match = re.match(r'^(.+?):(\d+)$', file_path)
        if match:
            file_path = match.group(1)
            line_number = match.group(2)

        # Resolve relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.root_path, file_path)

        # Normalize the path
        file_path = os.path.normpath(file_path)

        # Check if we're in a tmux session
        if not self._is_in_tmux():
            return (False, "Not running in tmux - cannot open file in overlay")

        # Build the neovim command
        if line_number:
            nvim_cmd = f"nvim +{line_number} '{file_path}'"
        else:
            nvim_cmd = f"nvim '{file_path}'"

        # Open in a new tmux window
        try:
            # Create a new tmux window with neovim
            tmux_cmd = ['tmux', 'new-window', '-n', 'nvim', nvim_cmd]
            subprocess.run(tmux_cmd, check=True)

            return (True, f"Opened {file_path}" + (f" at line {line_number}" if line_number else ""))
        except subprocess.CalledProcessError as e:
            return (False, f"Failed to open file in tmux: {str(e)}")
        except Exception as e:
            return (False, f"Error opening file: {str(e)}")

    def _is_in_tmux(self) -> bool:
        """
        Check if currently running inside a tmux session.

        Returns:
            bool: True if in tmux, False otherwise
        """
        return os.environ.get('TMUX') is not None
