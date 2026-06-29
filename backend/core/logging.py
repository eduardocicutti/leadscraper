import logging
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("DB_PATH", "banco.db")).resolve().parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "backend.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("lead_scraper")
