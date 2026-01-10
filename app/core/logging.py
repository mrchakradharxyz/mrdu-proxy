import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

from colorama import Fore, Style, init

init(autoreset=True)

APP_NAME = os.getenv("APP_NAME", "university_proxy")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # text | json
USE_COLORS = os.getenv("LOG_COLORS", "true").lower() == "true"

LOG_LEVEL = logging.DEBUG if DEBUG_MODE else logging.INFO

# =====================
# LOGGER CORE
# =====================
logger = logging.getLogger(APP_NAME)
logger.setLevel(LOG_LEVEL)
logger.handlers.clear()
logger.propagate = False

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(LOG_LEVEL)


# =====================
# FORMATTERS
# =====================
class TextFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level = record.levelname.ljust(8)
        msg = record.getMessage()

        if USE_COLORS:
            if record.levelno == logging.DEBUG:
                msg = Fore.CYAN + msg
            elif record.levelno == logging.INFO:
                msg = Fore.GREEN + msg
            elif record.levelno == logging.WARNING:
                msg = Fore.YELLOW + msg
            elif record.levelno >= logging.ERROR:
                msg = Fore.RED + Style.BRIGHT + msg

        return f"{ts} | {level} | {APP_NAME} | {msg}{Style.RESET_ALL}"


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "app": APP_NAME,
                "message": record.getMessage(),
            }
        )


handler.setFormatter(JSONFormatter() if LOG_FORMAT == "json" else TextFormatter())
logger.addHandler(handler)


# =====================
# SAVE LOG (EXTENSIBLE)
# =====================
def save_log(
    *,
    level: str,
    message: str,
    ip: Optional[str] = None,
    user: Optional[str] = None,
    path: Optional[str] = None,
):
    """
    Central sink:
    - Write to file
    - Push to DB
    - Send to SIEM
    - Send to Loki / Kafka later
    """
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "app": APP_NAME,
        "ip": ip,
        "user": user,
        "path": path,
        "message": message,
    }

    # Example: file-based audit log
    with open("audit.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# =====================
# PUBLIC LOG API
# =====================
def debug(msg: str):
    logger.debug(msg)


def info(msg: str):
    logger.info(msg)


def warn(msg: str):
    logger.warning(msg)


def error(msg: str):
    logger.error(msg)


def critical(msg: str):
    logger.critical(msg)
