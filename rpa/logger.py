"""
Step 6 — Log

Configures logging to both console and a rotating log file in logs/.
All other modules use: logging.getLogger("rpa.<module>")
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    """Set up root logger with console + rotating file handler."""
    os.makedirs("logs", exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on re-init
    if root_logger.handlers:
        return

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(console_handler)

    # Rotating file handler (max 5 MB, keep 3 backups)
    file_handler = RotatingFileHandler(
        "logs/rpa_bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(file_handler)
