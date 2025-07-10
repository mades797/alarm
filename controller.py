#!/usr/bin/python3
"""
Alarm service controller module
"""
import logging
import os
import signal
import time

try:
    from RPi import GPIO
except (RuntimeError, ModuleNotFoundError):
    from Mock import GPIO
from systemd import journal

from common import get_logging_level, handle_termination


ALARM_CONTROL_PIN = 15

logger = logging.getLogger('alarm-controller')
logger.addHandler(journal.JournalHandler())
logger.setLevel(get_logging_level())


def set_up() -> None:
    """
    Set up the GPIO outputs

    :return:
    """
    logger.debug('Setting up GPIO input')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(ALARM_CONTROL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def start_service() -> None:
    """
    Start the alarm service

    :return:
    :raises AssertionError: If alarm service is not running
    """
    logger.info('Starting alarm service')
    os.system('systemctl restart alarm.service')
    time.sleep(1)
    assert alarm_service_running()
    logger.debug('Alarm service started successfully')


def stop_service() -> None:
    """
    Stop the alarm service

    :return:
    :raises AssertionError: If alarm service is still running
    """
    logger.info('Stoping alarm service')
    os.system('systemctl stop alarm.service')
    time.sleep(1)
    assert not alarm_service_running()
    logger.debug('Alarm service stopped successfully')


def clean_up() -> None:
    """
    Clean up the GPIO outputs

    :return:
    """
    GPIO.cleanup()
    logger.debug('Cleaning up GPIO inputs')


def control() -> None:
    """
    Controller main loop

    :return:
    """
    service_running = alarm_service_running()
    while True:
        try:
            pin_state = GPIO.input(ALARM_CONTROL_PIN)
            if pin_state == GPIO.LOW and not service_running:
                # Idle
                time.sleep(5)
            elif pin_state == GPIO.LOW and service_running:
                # Stop signal
                logger.info('Received signal to stop alarm service')
                stop_service()
                service_running = False
            elif pin_state == GPIO.HIGH and not service_running:
                # Wake up
                logger.info('Received signal to start alarm service')
                start_service()
                service_running = True
            else:
                # All is well. Do nothing
                time.sleep(0.25)
        except KeyboardInterrupt:
            clean_up()
            break



def alarm_service_running() -> bool:
    """
    Check if alarm service is running

    :return:
    """
    return os.system('systemctl status alarm.service') >> 8 == 0


def _handle_termination(_signum, _frame) -> None:
    """
    Handle SIGTERM signal.

    :param _signum: Not used
    :param _frame: Not used
    :return:
    """
    logger.info('Received SIGTERM')
    handle_termination(clean_up)


if __name__ == '__main__':  # pragma: no cover
    logger.info('Starting alarm-controller')
    signal.signal(signal.SIGTERM, _handle_termination)
    set_up()
    control()
