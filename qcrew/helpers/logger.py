""" """
from pathlib import Path
import sys

from loguru import logger

# log folder path is relative to project directory
LOG_FOLDER_NAME = "logs"
LOG_FOLDER_PATH = Path.cwd() / LOG_FOLDER_NAME

# remove default handlers
logger.remove()

# customise logging levels
logger.level("INFO", color="<white><bold>")
logger.level("SUCCESS", color="<green>")
logger.level("WARNING", color="<magenta>")
logger.level("ERROR", color="<red><bold>")


log_record_fmt = (  # customise log record format
    "<cyan>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</>  "
    "<lvl>[{level}]  [{module}]  -  {message}</>"
)

# register log sinks with loguru logger
logger.add(  # save up to "TRACE" level logs in a log file for debugging
    LOG_FOLDER_PATH / "session_{time:YYYY-MM-DD_HH-mm-ss}.log",  # new log file
    format=log_record_fmt,
    rotation="6 hours",  # current log file closed and new one started every 6 hours
    retention="1 week",  # log files created more than a week ago will be removed
    level="TRACE",
    backtrace=False,  # no need to save exception trace beyond catching point
)
logger.add(sys.stderr, format=log_record_fmt, level="INFO")  # send to users

logger.info("Logger activated")  # log first message
