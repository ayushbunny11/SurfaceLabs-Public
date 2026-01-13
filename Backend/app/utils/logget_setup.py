import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from app.core.configs.app_config import system_config

LOG_LEVEL = system_config["LOG_LEVEL"]
print(LOG_LEVEL)

# -----------------------------
# LOG DIRECTORY
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# -----------------------------
# FORMATTERS
# -----------------------------
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(module)s:%(lineno)d | %(message)s"
)
formatter = logging.Formatter(LOG_FORMAT)


def build_rotating_handler(filename_base: str) -> TimedRotatingFileHandler:
    """
    Creates a daily rotating logger handler.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{filename_base}_log_{current_date}.log"

    handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        when="midnight",    # rotate every day
        backupCount=7,     # keep last 14 days
        encoding="utf-8",
        utc=False,
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    return handler


# -----------------------------
# LOGGER FACTORY
# -----------------------------
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:     # avoid attaching duplicate handlers
        logger.setLevel(LOG_LEVEL)

        # console
        console = logging.StreamHandler()
        console.setLevel(LOG_LEVEL)
        console.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        logger.addHandler(console)

        # file
        # file
        file_handler = build_rotating_handler(name)
        file_handler.setLevel(LOG_LEVEL)  # allow debug
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger


# -----------------------------
# PUBLIC LOGGERS
# -----------------------------
app_logger = get_logger("app")
db_logger = get_logger("db")
ai_logger = get_logger("ai")
