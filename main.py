import multiprocessing

import uvicorn

from backend.api.app import create_app
from backend.core.logging import logger

app = create_app()

multiprocessing.freeze_support()

if __name__ == "__main__":
    logger.info("Starting FastAPI server on 127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
