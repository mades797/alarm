#!/usr/bin/python3
"""
Alarm monitoring main module
"""
import logging
import signal
import time

try:
    from RPi import GPIO
except (RuntimeError, ModuleNotFoundError):
    from Mock import GPIO
from systemd import journal

from common import get_logging_level, handle_termination

ALARM_DURATION = 5  # seconds
ALARM_SNOOZE = 1  # seconds
FAST_FLASH_TIME = 0.25  # seconds
SLOW_FLASH_TIME = 0.65  # seconds
ARM_TIME = 20  # seconds
RELAY_PIN = 8
LED_PIN = 11
SWITCH_PIN = 37

logger = logging.getLogger('alarm')
logger.addHandler(journal.JournalHandler())
logger.setLevel(get_logging_level())


def flash(interval: float, duration: int | None = None) -> None:
    """
    Flash the LED

    :param interval: Interval in seconds between flashes
    :param duration: Duration in seconds of the flashing. If not specified, will flash forever
    :return:
    """
    start_time = time.time()
    while True:
        try:
            GPIO.output(LED_PIN, GPIO.HIGH)
            time.sleep(interval)
            GPIO.output(LED_PIN, GPIO.LOW)
            time.sleep(interval)
            if duration is not None and (time.time() - start_time) >= duration:
                break
        except KeyboardInterrupt:
            logger.info('Caught CTRL-C')
            clean_up()
            break


def detect_switch_trigger() -> None:
    """
    Detect the switch being triggered. This function blocks until an event is received

    :return:
    """
    while True:
        if GPIO.input(SWITCH_PIN) == GPIO.LOW:
            # Ground on switch detected. Return
            logger.info('Switch triggered')
            return
        time.sleep(0.1)


def set_alarm() -> None:
    """
    Activate the alarm. The function waits 1 second before activating the alarm for 5 seconds.

    :return:
    """
    # Wait for 1 second then set the alarm for 5 seconds
    logger.info('Setting alarm')
    time.sleep(ALARM_SNOOZE)
    logger.debug('Setting relay pin to HIGH')
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    time.sleep(ALARM_DURATION)
    logger.debug('Setting relay pin to LOW')
    GPIO.output(RELAY_PIN, GPIO.LOW)


def set_up() -> None:
    """
    Set up the GPIO outputs

    :return:
    """
    logger.debug('Setting up GPIO outputs')
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def arm() -> None:
    """
    Arm the alarm. The function will set the LED to flashing during the arm time. It will activate the LED at the end.

    :return:
    """
    logger.info('Alarm arming started')
    flash(FAST_FLASH_TIME, ARM_TIME)
    GPIO.output(LED_PIN, GPIO.HIGH)
    logger.info('Alarm arming finished')


def clean_up() -> None:
    """
    Clean up the GPIO outputs

    :return:
    """
    GPIO.output(RELAY_PIN, GPIO.LOW)
    GPIO.output(LED_PIN, GPIO.LOW)
    GPIO.cleanup()
    logger.debug('Cleaning up GPIO outputs')


def monitor() -> None:
    """
    Monitor for mouse event. The function is blocking until a KeyboardInterrupt is raised. Then it will clean up the
    GPIO outputs before returning.

    :return:
    """
    while True:
        try:
            detect_switch_trigger()
            set_alarm()
        except KeyboardInterrupt:
            logger.info('Caught CTRL-C')
            clean_up()
            break


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
    logger.info('Starting alarm')
    signal.signal(signal.SIGTERM, _handle_termination)
    set_up()
    arm()
    monitor()
