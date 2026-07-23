"""
==========================================================
AI Recruitment Assistant
Version : 0.2
File    : services/logger.py
==========================================================
"""

import logging
from config.settings import LOG_FILE


def setup_logger():

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )

    logging.info("=" * 60)
    logging.info("Application Started")
    logging.info("=" * 60)

    return logging