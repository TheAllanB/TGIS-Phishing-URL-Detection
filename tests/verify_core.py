from src.core.config import settings
from src.core.logger import log
import os

def test_config():
    log.info("Testing Configuration Loader...")
    log.debug(f"DEBUG Mode: {settings.DEBUG}")
    log.info(f"Database Host: {settings.DB_HOST}")
    log.info(f"Database Port: {settings.DB_PORT}")
    log.info(f"Redis Host: {settings.REDIS_HOST}")
    log.info(f"Model Path: {settings.MODEL_PATH}")
    log.info(f"Computed DB URL: {settings.database_url}")
    log.info(f"Computed Redis URL: {settings.redis_url}")

def test_logging():
    log.info("Testing Logging System...")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    try:
        1 / 0
    except Exception:
        log.exception("Caught an intentional exception for testing.")
    
    # Check if file exists
    if os.path.exists("logs/app.log"):
        log.success("Verification Successful: logs/app.log file was created.")
    else:
        log.error("Verification Failed: logs/app.log file was NOT created.")

if __name__ == "__main__":
    test_config()
    test_logging()
