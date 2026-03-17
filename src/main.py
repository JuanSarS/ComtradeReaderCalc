"""Desktop entry point for the embedded COMTRADE Pro application."""

import sys
from pathlib import Path

# Add project root to sys.path so src package can be found
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui.desktop.server import launch_desktop_app


def main() -> int:
    """Launch the PyQt desktop shell with the embedded web UI."""
    return launch_desktop_app()


if __name__ == "__main__":
    sys.exit(main())
