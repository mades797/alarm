"""
Alarm monitoring tests module
"""
from unittest.mock import call, patch, MagicMock
from unittest import TestCase

from common import handle_termination
from controller import (
    _handle_termination as controller_handle_termination,
    alarm_service_running,
    clean_up as controller_clean_up,
    control,
    set_up as controller_set_up,
    start_service,
    stop_service,
    ALARM_CONTROL_PIN,
)
from main import (
    _handle_termination as main_handle_termination,
    arm,
    detect_mouse_movement,
    flash,
    monitor,
    set_alarm,
    set_up as main_set_up,
    FAST_FLASH_TIME,
    SLOW_FLASH_TIME,
    ARM_TIME,
    RELAY_PIN,
    LED_PIN,
)

class AlarmTest(TestCase):
    """
    Test class for `main`
    """

    @patch('main.InputDevice')
    def test_detect_mouse_movement(self, mock_intput_device):
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
    def test_detect_mouse_movement_error(self, mock_intput_device, mock_flash):
        """
        Test for `detect_mouse_movement` when the device is not found
        """
        mock_intput_device.side_effect = FileNotFoundError
        detect_mouse_movement()
        mock_flash.assert_called_with(SLOW_FLASH_TIME)


    @patch('main.GPIO')
    @patch('main.time')
    def test_set_alarm(self, _mock_time, mock_gpio):
        """
        Test for `set_alarm`
        """
        set_alarm()
        mock_gpio.output.assert_has_calls([call(RELAY_PIN, mock_gpio.HIGH), call(RELAY_PIN, mock_gpio.LOW)])


    @patch('main.GPIO')
    def test_set_up(self, mock_gpio):
        """
        Test for `set_up`
        """
        main_set_up()
        mock_gpio.setmode.assert_has_calls([call(mock_gpio.BOARD)])
        mock_gpio.setup.assert_has_calls([
            call(RELAY_PIN, mock_gpio.OUT, initial=mock_gpio.LOW),
            call(LED_PIN, mock_gpio.OUT, initial=mock_gpio.LOW)
        ])


    @patch('main.flash')
    @patch('main.GPIO')
    @patch('main.time')
    def test_arm(self, _mock_time, mock_gpio, mock_flash):
        """
        Test for `arm`
        """
        arm()
        mock_flash.assert_called_with(FAST_FLASH_TIME, ARM_TIME)
        mock_gpio.output.assert_called_with(LED_PIN, mock_gpio.HIGH)


    @patch('main.GPIO')
    def test_monitor(self, mock_gpio):
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
    @patch('main.GPIO')
    @patch('main.time')
    def test_flash_fast_forever(self, mock_time, mock_gpio, mock_cleanup) -> None:
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
    def test_flash_slow_duration(self, mock_time, mock_gpio, mock_cleanup) -> None:
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

    @patch('main.handle_termination')
    @patch('main.clean_up')
    def test_handle_termination(self, mock_clean_up, mock_handle_termination) -> None:
        """
        Test for `_handle_termination`
        """
        main_handle_termination(MagicMock(), MagicMock())
        mock_handle_termination.assert_called_once_with(mock_clean_up)


class ControllerTestCase(TestCase):
    """
    Test for `controller`
    """

    @patch('controller.GPIO')
    def test_set_up(self, mock_gpio) -> None:
        """
        Test for `set_up`
        """
        controller_set_up()
        mock_gpio.setmode.assert_called_once_with(mock_gpio.BOARD)
        mock_gpio.setup.assert_called_once_with(ALARM_CONTROL_PIN, mock_gpio.IN, pull_up_down=mock_gpio.PUD_UP)

    @patch('controller.os')
    @patch('controller.time')
    def test_start_service_ok(self, mock_time, mock_os) -> None:
        """
        Test for `start_service`
        """

        with patch('controller.alarm_service_running', return_value=True) as mock_alarm_service_running:
            start_service()
            mock_os.system.assert_called_once_with('systemctl restart alarm.service')
            mock_time.sleep.assert_called_once_with(1)
            mock_alarm_service_running.assert_called_once()

    @patch('controller.os')
    @patch('controller.time')
    def test_start_service_error(self, mock_time, mock_os) -> None:
        """
        Test for `start_service` when the service is not started
        """

        with patch('controller.alarm_service_running', return_value=False) as mock_alarm_service_running:
            with self.assertRaises(AssertionError):
                try:
                    start_service()
                except AssertionError:
                    mock_os.system.assert_called_once_with('systemctl restart alarm.service')
                    mock_time.sleep.assert_called_once_with(1)
                    mock_alarm_service_running.assert_called_once()
                    raise

    @patch('controller.os')
    @patch('controller.time')
    def test_stop_service_ok(self, mock_time, mock_os) -> None:
        """
        Test for `stop_service`
        """

        with patch('controller.alarm_service_running', return_value=False) as mock_alarm_service_running:
            stop_service()
            mock_os.system.assert_called_once_with('systemctl stop alarm.service')
            mock_time.sleep.assert_called_once_with(1)
            mock_alarm_service_running.assert_called_once()

    @patch('controller.os')
    @patch('controller.time')
    def test_stop_service_error(self, mock_time, mock_os) -> None:
        """
        Test for `stop_service` when the service is not stopped
        """

        with patch('controller.alarm_service_running', return_value=True) as mock_alarm_service_running:
            with self.assertRaises(AssertionError):
                try:
                    stop_service()
                except AssertionError:
                    mock_os.system.assert_called_once_with('systemctl stop alarm.service')
                    mock_time.sleep.assert_called_once_with(1)
                    mock_alarm_service_running.assert_called_once()
                    raise

    @patch('controller.GPIO')
    def test_clean_up(self, mock_gpio) -> None:
        """
        Test for `clean_up`
        """
        controller_clean_up()
        mock_gpio.cleanup.assert_called_once()

    @patch('controller.GPIO')
    @patch('controller.alarm_service_running')
    @patch('controller.start_service')
    @patch('controller.time')
    @patch('controller.clean_up')
    def test_control_1(self, mock_clean_up, mock_time, mock_start_service, mock_alarm_service_running, mock_gpio) -> None:
        """
        Test for `control` scenario 1.

        Initially:
            - Service is not running
            - Pin is LOW
        Then:
            - 5 iterations
            - Pin is HIGH
            - 5 iterations
            - KeyboardInterrupt is raised
        Expected:
            - Service is started when pin is HIGH
            - clean_up() is called at KeyboardInterrupt
        """
        mock_gpio.input.side_effect = [mock_gpio.LOW] * 5 + [mock_gpio.HIGH] * 6 + [KeyboardInterrupt]
        mock_alarm_service_running.return_value = False
        control()
        mock_time.sleep.assert_has_calls([call(5)] * 5 + [call(0.25)] * 5)
        mock_start_service.assert_called_once()
        mock_clean_up.assert_called_once()

    @patch('controller.GPIO')
    @patch('controller.alarm_service_running')
    @patch('controller.stop_service')
    @patch('controller.time')
    @patch('controller.clean_up')
    def test_control_2(self, mock_clean_up, mock_time, mock_stop_service, mock_alarm_service_running, mock_gpio) -> None:
        """
        Test for `control` scenario 2.

        Initially:
            - Service is running
            - Pin is HIGH
        Then:
            - 5 iterations
            - Pin is LOW
            - 5 iterations
            - KeyboardInterrupt is raised
        Expected:
            - Service is stopped when pin is LOW
            - clean_up() is called at KeyboardInterrupt
        """
        mock_gpio.input.side_effect = [mock_gpio.HIGH] * 5 + [mock_gpio.LOW] * 6 + [KeyboardInterrupt]
        mock_alarm_service_running.return_value = True
        control()
        mock_time.sleep.assert_has_calls([call(0.25)] * 5 + [call(5)] * 5)
        mock_stop_service.assert_called_once()
        mock_clean_up.assert_called_once()

    @patch('controller.os')
    def test_alarm_service_running_zero(self, mock_os) -> None:
        """
        Test for `alarm_service_running` when service is running and `system` returns 0
        """
        mock_os.system.return_value = 0
        assert alarm_service_running() is True
        mock_os.system.assert_called_once_with('systemctl status alarm.service')

    @patch('controller.os')
    def test_alarm_service_running_non_zero(self, mock_os) -> None:
        """
        Test for `alarm_service_running` when service is running and `system` returns non-zero
        """
        mock_os.system.return_value = 255
        assert alarm_service_running() is True
        mock_os.system.assert_called_once_with('systemctl status alarm.service')

    @patch('controller.os')
    def test_alarm_service_not_running(self, mock_os) -> None:
        """
        Test for `alarm_service_running` when service is not running
        """
        mock_os.system.return_value = 256
        assert alarm_service_running() is False
        mock_os.system.assert_called_once_with('systemctl status alarm.service')

    @patch('controller.handle_termination')
    @patch('controller.clean_up')
    def test_handle_termination(self, mock_clean_up, mock_handle_termination) -> None:
        """
        Test for `_handle_termination`
        """
        controller_handle_termination(MagicMock(), MagicMock())
        mock_handle_termination.assert_called_once_with(mock_clean_up)


@patch('common.sys')
def test_handle_termination(mock_sys) -> None:
    """
    Test for `handle_termination`
    """
    mock_cleanup = MagicMock()
    handle_termination(mock_cleanup)
    mock_cleanup.assert_called()
    mock_sys.exit.assert_called_with(0)
