"""
Configures loguru's logger.
"""
import sys
from pathlib import Path

from loguru import logger

# log folder path is relative to project directory
LOG_FOLDER_NAME = "logs"
LOG_FOLDER_PATH = Path.cwd() / LOG_FOLDER_NAME

# customize level colors
logger.level("DEBUG", color="<cyan>")
logger.level("INFO", color="<white>")
logger.level("SUCCESS", color="<blue>")
logger.level("WARNING", color="<magenta>")
logger.level("ERROR", color="<red>")

# specify record format for logs saved to file and displayed to user
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:^7} | {name}:{function}:{line} - {message}"
)

# register log sink with loguru logger
# new log file will be created every day at midnight
logger.add(
    LOG_FOLDER_PATH / "log_{time:YYYYMMDD}.log",
    rotation="00:00",
    level="DEBUG",
    format=LOG_FORMAT,
)

logger.info("Logger activated")
