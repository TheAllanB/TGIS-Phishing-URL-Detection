import sys
import logging
from pprint import pformat
from loguru import logger
from src.core.config import settings

class InterceptHandler(logging.Handler):
    """
    Standard Python logging interceptor for Loguru.
    Captures all logs from third-party libraries (e.g., FastAPI, XGBoost, NetworkX).
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_logging():
    """
    Configure Loguru with standard settings.
    - Standardized log level from config.
    - Console output with colorizing.
    - File output with rotation and retention.
    - Intercepts all standard logging calls.
    """
    # Remove default Loguru handler
    logger.remove()

    # Define log format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add Console Handler
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=log_format,
        colorize=True,
    )

    # Add File Handler
    logger.add(
        "logs/app.log",
        level=settings.LOG_LEVEL,
        format=log_format,
        rotation="10 MB",
        retention="10 days",
        compression="zip",
    )

    # Intercept Standard Logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Suppress verbose logs from some libraries if needed
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    
    return logger

# Initialize logger on module import
log = setup_logging()
