import logging
import sys
import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()
ENV = os.getenv("ENV", default="env").lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

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

def setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
        serialize=True if ENV == "prod" else False
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    loggers_to_intercept = ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine")
    for logger_name in loggers_to_intercept:
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

setup_logging()
__all__ = ["logger"]