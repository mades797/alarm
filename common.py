"""
Alarm service common methods
"""
import logging
import os
import sys
from typing import Callable


def get_logging_level() -> int:
    """
    Get logging level

    :return:
    """
    return {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }[os.environ.get('ALARM_LOG_LEVEL', 'INFO').upper()]


def handle_termination(clean_up: Callable = lambda: None) -> None:
    """
    Handle SIGTERM signal.

    :param clean_up: Not used
    :return:
    """
    clean_up()
    sys.exit(0)
