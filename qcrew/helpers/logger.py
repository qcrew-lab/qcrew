"""
Configures loguru's logger.
Provides a decorator for logging (and timing) methods.
"""
import functools
from pathlib import Path
import time
import sys

from loguru import logger

# log folder path is relative to project directory
LOG_FOLDER_NAME = "logs"
LOG_FOLDER_PATH = Path.cwd() / LOG_FOLDER_NAME

# remove default handlers
logger.remove()

# register log sinks with loguru logger
logger.add(
    LOG_FOLDER_PATH / "session_{time:YYYY-MM-DD_HH-mm-ss}.log",  # new log file
    rotation="6 hours",  # current log file closed and new one started every 6 hours
    retention="1 week",  # log files created more than a week ago will be removed
    level="TRACE",  # save up to "TRACE" level logs for debugging
    backtrace=False,  # no need to save exception trace beyond catching point
)
logger.add(sys.stderr, level="INFO")  # send logs with level "INFO" or higher to users

logger.info("Logger activated")  # log first message

# decorator to log entry, exit, and execution time of functions for debugging
# optional arguments to specify level, log function args and/or result
def logit(func=None, *, level="TRACE", with_args=False, with_result=False):
    if func is None:  # decorator is called with arguments
        return functools.partial(
            logit, level=level, with_args=with_args, with_result=with_result
        )

    module_ = func.__module__
    name_ = func.__name__

    @functools.wraps(func)
    def logit_wrapper(*args, **kwargs):
        if with_args:
            logger.log(
                level,
                "{}:{} called with args={} and kwargs={}",
                module_,
                name_,
                args,
                kwargs,
            )
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        logger.log(level, "{}:{} executed in {:.7f}s", module_, name_, elapsed_time)
        if with_result:
            logger.log(level, "{}:{} produced {}", module_, name_, result)
        return result

    return logit_wrapper
