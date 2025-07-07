"""
Alarm monitoring tests module
"""
from unittest.mock import call, patch, MagicMock

from main import (
    arm,
    detect_mouse_movement,
    flash,
    handle_termination,
    monitor,
    set_alarm,
    set_up,
    FAST_FLASH_TIME,
    SLOW_FLASH_TIME,
    ARM_TIME,
    RELAY_PIN,
    LED_PIN,
)

@patch('main.InputDevice')
def test_detect_mouse_movement(mock_intput_device):
    """
    Test for `detect_mouse_movement`
    """
    mock_device = MagicMock()
    mock_intput_device.return_value = mock_device
    mock_event = MagicMock(value=5)
    mock_device.read_loop = MagicMock()
    mock_device.read_loop.return_value.__iter__.return_value = iter([mock_event])
    detect_mouse_movement()


@patch('main.flash')
@patch('main.InputDevice')
def test_detect_mouse_movement_error(mock_intput_device, mock_flash):
    """
    Test for `detect_mouse_movement` when the device is not found
    """
    mock_intput_device.side_effect = FileNotFoundError
    detect_mouse_movement()
    mock_flash.assert_called_with(SLOW_FLASH_TIME)


@patch('main.GPIO')
@patch('main.time')
def test_set_alarm(_mock_time, mock_gpio):
    """
    Test for `set_alarm`
    """
    set_alarm()
    mock_gpio.output.assert_has_calls([call(RELAY_PIN, mock_gpio.HIGH), call(RELAY_PIN, mock_gpio.LOW)])


@patch('main.GPIO')
def test_set_up(mock_gpio):
    """
    Test for `set_up`
    """
    set_up()
    mock_gpio.setmode.assert_has_calls([call(mock_gpio.BOARD)])
    mock_gpio.setup.assert_has_calls([
        call(RELAY_PIN, mock_gpio.OUT, initial=mock_gpio.LOW),
        call(LED_PIN, mock_gpio.OUT, initial=mock_gpio.LOW)
    ])


@patch('main.flash')
@patch('main.GPIO')
@patch('main.time')
def test_arm(_mock_time, mock_gpio, mock_flash):
    """
    Test for `arm`
    """
    arm()
    mock_flash.assert_called_with(FAST_FLASH_TIME, ARM_TIME)
    mock_gpio.output.assert_called_with(LED_PIN, mock_gpio.HIGH)


@patch('main.GPIO')
def test_monitor(mock_gpio):
    """
    Test for `monitor`. The test will set the alarm 3 times. A KeyboardInterrupt is received during the 4th iteration.
    """
    with patch('main.detect_mouse_movement') as mock_detect_mouse_movement, patch('main.set_alarm') as mock_set_alarm:
        def detect_mouse_movement_side_effect():
            nonlocal mock_detect_mouse_movement
            if mock_detect_mouse_movement.call_count >= 4:
                raise KeyboardInterrupt

        mock_detect_mouse_movement.side_effect = detect_mouse_movement_side_effect
        monitor()
        assert mock_detect_mouse_movement.call_count == 4
        assert mock_set_alarm.call_count == 3
        mock_gpio.output.assert_has_calls([call(RELAY_PIN, mock_gpio.LOW), call(LED_PIN, mock_gpio.LOW)])
        mock_gpio.cleanup.assert_called()


@patch('main.clean_up')
@patch('main.sys')
def test_handle_termination(mock_sys, mock_cleanup) -> None:
    """
    Test for `handle_termination`
    """
    handle_termination(MagicMock(), MagicMock())
    mock_cleanup.assert_called()
    mock_sys.exit.assert_called_with(0)


@patch('main.clean_up')
@patch('main.GPIO')
@patch('main.time')
def test_flash_fast_forever(mock_time, mock_gpio, mock_cleanup) -> None:
    """
    Test for `flash` when no duration is provided. The function will flash 10 times before a KeyboardInterrupt is
    received.
    """

    def sleep_side_effect(*_args):
        nonlocal mock_time
        if mock_time.sleep.call_count > 20:
            raise KeyboardInterrupt
    mock_time.sleep.side_effect = sleep_side_effect
    flash(FAST_FLASH_TIME)
    mock_time.sleep.assert_has_calls([call(FAST_FLASH_TIME)] * 20)
    mock_gpio.output.assert_has_calls([call(LED_PIN, mock_gpio.HIGH), call(LED_PIN, mock_gpio.LOW)] * 10)
    mock_cleanup.assert_called()


@patch('main.clean_up')
@patch('main.GPIO')
@patch('main.time')
def test_flash_slow_duration(mock_time, mock_gpio, mock_cleanup) -> None:
    """
    Test for `flash` when a duration is provided. The function will flash 5 times before the duration is reached.
    """
    mock_time.time.return_value.__sub__.return_value = 5

    def sleep_side_effect(*_args):
        nonlocal mock_time
        if mock_time.sleep.call_count > 10:
            mock_time.time.return_value.__sub__.return_value = 100
    mock_time.sleep.side_effect = sleep_side_effect
    flash(SLOW_FLASH_TIME, 10)
    mock_time.sleep.assert_has_calls([call(SLOW_FLASH_TIME)] * 10)
    mock_gpio.output.assert_has_calls([call(LED_PIN, mock_gpio.HIGH), call(LED_PIN, mock_gpio.LOW)] * 5)
    mock_cleanup.assert_not_called()
