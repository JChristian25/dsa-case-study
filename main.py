"""Main entry point to run the CLI or showcase.

Authors:
- See submodules for contributors
"""

from app.cli import run_menu
from app.showcase import run_showcase

CONFIG_PATH = "config.json"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_menu()
    else:
        run_showcase(CONFIG_PATH)