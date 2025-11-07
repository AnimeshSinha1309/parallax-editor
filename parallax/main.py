"""
Entry point for the Parallax text editor.
"""

import sys
from pathlib import Path
from parallax.app import ParallaxApp


def main():
    """
    Main entry point for Parallax.

    Usage:
        python -m parallax.main [directory]
    """
    # Get the root directory from command line args or use current directory
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        root_path = "."

    # Resolve to absolute path
    root_path = str(Path(root_path).resolve())

    # Create and run the app
    app = ParallaxApp(root_path=root_path)
    app.run()


if __name__ == "__main__":
    main()
