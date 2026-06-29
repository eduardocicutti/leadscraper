import os
import sys
from pathlib import Path


def configure_playwright_path() -> None:
    if os.getenv("PLAYWRIGHT_BROWSERS_PATH"):
        return

    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).resolve().parent / "ms-playwright"
        if bundled.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(bundled)
