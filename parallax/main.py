"""
Entry point for the Parallax text editor.
"""

import argparse
from pathlib import Path
from parallax.app import ParallaxApp
from utils.context import GlobalPreferenceContext


def main():
    """
    Main entry point for Parallax.

    Usage:
        python -m parallax.main [--scope DIRECTORY] [--plan PLAN_FILE]
    """
    parser = argparse.ArgumentParser(description="Parallax - AI-assisted text editor")
    parser.add_argument(
        "--scope",
        type=str,
        default=".",
        help="Root directory path for the scope (default: current directory)"
    )
    parser.add_argument(
        "--plan",
        type=str,
        default=None,
        help="Path to the markdown plan file being edited"
    )

    args = parser.parse_args()

    # Resolve scope root to absolute path
    scope_root = str(Path(args.scope).resolve())

    # Resolve plan path to absolute path if provided
    plan_path = None
    if args.plan:
        plan_path = str(Path(args.plan).resolve())

    # Create global preference context
    global_context = GlobalPreferenceContext(
        scope_root=scope_root,
        plan_path=plan_path
    )

    # Create and run the app
    app = ParallaxApp(global_context=global_context)
    app.run()


if __name__ == "__main__":
    main()
