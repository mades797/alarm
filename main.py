"""
Alarm monitoring main module
"""
import time

from evdev import InputDevice
try:
    from RPi import GPIO
except (RuntimeError, ModuleNotFoundError):
    from Mock import GPIO

ALARM_DURATION = 5  # seconds
ALARM_SNOOZE = 1  # seconds
ARM_FLASH_TIME = 0.5  # seconds
ARM_TIME = 30  # seconds
RELAY_PIN = 13
LED_PIN = 11

def detect_mouse_movement() -> None:
    """
    Detect a mouse movement. This function blocks until an event is received

    :return:
    """
    dev = InputDevice('/dev/input/by-id/usb-1bcf_USB_Optical_Mouse-event-mouse')
    for event in dev.read_loop():
        print(f'Event: {event} value: {event.value}')
        if event.value != 0:
            break


def set_alarm() -> None:
    """
    Activate the alarm. The function waits 1 second before activating the alarm for 5 seconds.

    :return:
    """
    # Wait for 1 second then set the alarm for 5 seconds
    print('Start of set_alarm')
    time.sleep(ALARM_SNOOZE)
    print('Setting relay pin to HIGH')
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    time.sleep(ALARM_DURATION)
    print('Setting relay pin to LOW')
    GPIO.output(RELAY_PIN, GPIO.LOW)


def set_up() -> None:
    """
    Set up the GPIO outputs

    :return:
    """
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.LOW)

def arm() -> None:
    """
    Arm the alarm. The function will set the LED to flashing during the arm time. It will activate the LED at the end.

    :return:
    """
    for _ in range(int(ARM_TIME / 2)):
        GPIO.output(LED_PIN, GPIO.HIGH)
        time.sleep(ARM_FLASH_TIME)
        GPIO.output(LED_PIN, GPIO.LOW)
        time.sleep(ARM_FLASH_TIME)
    GPIO.output(LED_PIN, GPIO.HIGH)


def monitor() -> None:
    """
    Monitor for mouse event. The function is blocking until a KeyboardInterrupt is raised. Then it will clean up the
    GPIO outputs before returning.

    :return:
    """
    while True:
        try:
            detect_mouse_movement()
            set_alarm()
        except KeyboardInterrupt:
            print('Keyboard interrupt')
            GPIO.output(RELAY_PIN, GPIO.LOW)
            GPIO.output(LED_PIN, GPIO.LOW)
            GPIO.cleanup()
            break


if __name__ == '__main__':
    set_up()
    arm()
    monitor()
