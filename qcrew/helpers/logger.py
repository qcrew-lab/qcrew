"""
Configures loguru's logger.
"""
from pathlib import Path

from loguru import logger

# log folder path is relative to project directory
LOG_FOLDER_NAME = "logs"
LOG_FOLDER_PATH = Path.cwd() / LOG_FOLDER_NAME

# register log sink with loguru logger
logger.add(
    LOG_FOLDER_PATH / "log_{time:YYYYMMDD}.log",
    rotation="00:00",  # new log file will be created every day at midnight
)

logger.debug("Logger activated")  # log first message
