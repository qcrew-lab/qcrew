""" """

from pathlib import Path
import sys

from loguru import logger

LOG_FOLDER_NAME = "logs"  # TODO make cwd() ALWAYS relative to workspace folder
LOG_FOLDER_PATH = Path.cwd() / LOG_FOLDER_NAME  # relative to project directory

logger.remove()  # remove default handlers

# customise logging levels
logger.level("INFO", color="<white>")
logger.level("SUCCESS", color="<green>")
logger.level("WARNING", color="<magenta>")
logger.level("ERROR", color="<red>")


log_record_format = (  # customise log record format
    "<cyan>[{time:YY-MM-DD HH:mm:ss}]</> " "<lvl>{level: <7} [{module}] - {message}</>"
)

# register log sinks with loguru logger
logger.add(  # save up to "TRACE" level logs in a log file for debugging
    LOG_FOLDER_PATH / "session.log",
    format=log_record_format,
    rotation="24 hours",  # current log file closed and new one started every 24 hours
    retention="1 week",  # log files created more than a week ago will be removed
    level="TRACE",
    backtrace=False,  # no need to save exception trace beyond catching point
)
logger.add(  # send logged messages to users
    sys.stderr, format=log_record_format, level="INFO", backtrace=False, diagnose=True
)

logger.info("Logger activated")  # log first message
