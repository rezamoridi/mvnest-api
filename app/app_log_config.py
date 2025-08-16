import time
import logging
import sys
import os
import threading
import requests
from dotenv import load_dotenv
from loguru import logger
# Load environment variables
load_dotenv()
ENV = os.getenv("ENV", default="env").lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BALE_LOG_LEVEL=os.getenv("BALE_LOG_LEVEL", "ERROR").upper()

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def bale_sink(message: str):
    """Send log message to Bale asynchronously."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("BOT_TOKEN or CHAT_ID not set. Bale sink skipped.")
        return

    def _send():
        url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
        for _ in range(3):  # retry 3 times
            try:
                requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
                return
            except requests.RequestException as e:
                logger.warning(f"[Bale sink retry] {e}")
                time.sleep(2)
        logger.error(f"[Bale sink failed] after retries")

    threading.Thread(target=_send, daemon=True).start()


def setup_logging():
    logger.remove()

    # Terminal logging (always)
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
        serialize=True if ENV == "prod" else False
    )

    # Bale logging (errors only)
    if BOT_TOKEN and CHAT_ID:
        logger.add(bale_sink, level=BALE_LOG_LEVEL)

    # Intercept other loggers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    loggers_to_intercept = ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine")
    for logger_name in loggers_to_intercept:
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False


setup_logging()
__all__ = ["logger"]