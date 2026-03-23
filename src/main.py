"""Entry point for RuneLite Profile Manager."""

import sys
from pathlib import Path

# Add project root to sys.path so src.* imports work when running directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.gui.app import ProfileManagerApp


def main():
    app = ProfileManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
