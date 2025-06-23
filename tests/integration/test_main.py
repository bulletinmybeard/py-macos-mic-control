import logging
import signal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mic_control.__main__ import MicrophoneController, main, parse_args, setup_logging
from mic_control.config import Config


class TestMicrophoneController:
    """Test cases for MicrophoneController class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config(
            target_volume=80,
            active_interval=1,
            idle_interval=2,
            call_interval=5,
            log_path=Path("/tmp/test.log"),
        )

    @pytest.fixture
    def mock_audio_monitor(self):
        """Mock AudioMonitor."""
        with patch("mic_control.__main__.AudioMonitor") as mock:
            instance = Mock()
            mock.return_value = instance
            yield instance

    @pytest.fixture
    def mock_volume_controller(self):
        """Mock get_volume_controller."""
        with patch("mic_control.__main__.get_volume_controller") as mock:
            controller = Mock()
            mock.return_value = controller
            yield controller

    def test_initialization(self, config, mock_audio_monitor, mock_volume_controller):
        """Test controller initialization."""
        controller = MicrophoneController(config)

        assert controller.config == config
        assert controller.running is True
        assert controller.in_call is False
        assert controller.last_call_check == 0.0

    def test_signal_handler(self, config, mock_audio_monitor, mock_volume_controller):
        """Test signal handler stops the controller."""
        controller = MicrophoneController(config)

        controller._signal_handler(signal.SIGINT, None)

        assert controller.running is False

    @patch("mic_control.__main__.time.sleep")
    @patch("mic_control.__main__.time.time")
    def test_run_normal_operation(
        self, mock_time, mock_sleep, config, mock_audio_monitor, mock_volume_controller
    ):
        """Test normal operation of the run loop."""
        controller = MicrophoneController(config)

        # Mock time progression
        mock_time.side_effect = [0, 6, 7]  # Trigger call check on second iteration

        # Mock detect_call_activity results
        mock_audio_monitor.detect_call_activity.side_effect = [True, False]

        # Mock volume operations
        mock_volume_controller.get_volume.return_value = 70
        mock_volume_controller.set_volume.return_value = True

        # Stop after two iterations
        call_count = 0

        def stop_after_two(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                controller.running = False

        mock_sleep.side_effect = stop_after_two

        controller.run()

        # Verify call detection was performed
        assert mock_audio_monitor.detect_call_activity.call_count >= 1

        # Verify volume was adjusted during call
        mock_volume_controller.get_volume.assert_called()
        mock_volume_controller.set_volume.assert_called_with(80)

        # Verify cleanup was called
        mock_audio_monitor.cleanup.assert_called_once()

    def test_handle_active_call_volume_adjustment(
        self, config, mock_audio_monitor, mock_volume_controller
    ):
        """Test volume adjustment during active call."""
        controller = MicrophoneController(config)

        mock_volume_controller.get_volume.return_value = 60
        mock_volume_controller.set_volume.return_value = True

        controller._handle_active_call()

        mock_volume_controller.get_volume.assert_called_once()
        mock_volume_controller.set_volume.assert_called_once_with(80)

    def test_handle_active_call_volume_already_correct(
        self, config, mock_audio_monitor, mock_volume_controller
    ):
        """Test no adjustment when volume is already correct."""
        controller = MicrophoneController(config)

        mock_volume_controller.get_volume.return_value = 80

        controller._handle_active_call()

        mock_volume_controller.get_volume.assert_called_once()
        mock_volume_controller.set_volume.assert_not_called()

    def test_handle_active_call_volume_adjustment_fails(
        self, config, mock_audio_monitor, mock_volume_controller
    ):
        """Test handling of failed volume adjustment."""
        controller = MicrophoneController(config)

        mock_volume_controller.get_volume.return_value = 60
        mock_volume_controller.set_volume.return_value = False

        controller._handle_active_call()

        mock_volume_controller.set_volume.assert_called_once_with(80)

    @patch("mic_control.__main__.time.sleep")
    def test_run_with_exception(
        self, mock_sleep, config, mock_audio_monitor, mock_volume_controller
    ):
        """Test that exceptions in run loop trigger cleanup."""
        controller = MicrophoneController(config)

        # Make detect_call_activity raise an exception
        mock_audio_monitor.detect_call_activity.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            controller.run()

        # Cleanup should still be called
        mock_audio_monitor.cleanup.assert_called_once()


class TestParseArgs:
    """Test command line argument parsing."""

    def test_parse_args_defaults(self):
        """Test parsing with no arguments."""
        with patch("sys.argv", ["mic-control"]):
            args = parse_args()

        assert args.target_volume is None
        assert args.active_interval is None
        assert args.idle_interval is None
        assert args.call_interval is None
        assert args.log_path is None
        assert args.config is None
        assert args.save_config is False
        assert args.debug is False

    def test_parse_args_all_options(self):
        """Test parsing with all arguments."""
        with patch(
            "sys.argv",
            [
                "mic-control",
                "--target-volume",
                "75",
                "--active-interval",
                "5",
                "--idle-interval",
                "20",
                "--call-interval",
                "45",
                "--log-path",
                "/tmp/mic.log",
                "--config",
                "/tmp/config.json",
                "--save-config",
                "--debug",
            ],
        ):
            args = parse_args()

        assert args.target_volume == 75
        assert args.active_interval == 5
        assert args.idle_interval == 20
        assert args.call_interval == 45
        assert args.log_path == "/tmp/mic.log"
        assert args.config == "/tmp/config.json"
        assert args.save_config is True
        assert args.debug is True


class TestSetupLogging:
    """Test logging setup."""

    @patch("mic_control.__main__.logging.basicConfig")
    @patch("mic_control.__main__.logging.getLogger")
    def test_setup_logging_info_level(self, mock_get_logger, mock_basic_config):
        """Test logging setup with INFO level."""
        config = Config(log_level="INFO", log_path=Path("/tmp/test.log"))

        setup_logging(config)

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == logging.INFO

    @patch("mic_control.__main__.logging.basicConfig")
    @patch("mic_control.__main__.logging.getLogger")
    def test_setup_logging_debug_level(self, mock_get_logger, mock_basic_config):
        """Test logging setup with DEBUG level."""
        config = Config(log_level="DEBUG", log_path=Path("/tmp/test.log"))

        setup_logging(config)

        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == logging.DEBUG


class TestMain:
    """Test main function."""

    @patch("mic_control.__main__.MicrophoneController")
    @patch("mic_control.__main__.setup_logging")
    @patch("mic_control.__main__.validate_log_path")
    @patch("mic_control.__main__.Config.load")
    @patch("mic_control.__main__.parse_args")
    def test_main_normal_operation(
        self,
        mock_parse_args,
        mock_config_load,
        mock_validate_log,
        mock_setup_logging,
        mock_controller_class,
    ):
        """Test normal operation of main function."""
        # Setup mocks
        args = Mock(debug=False, save_config=False)
        mock_parse_args.return_value = args

        config = Config()
        mock_config_load.return_value = config
        mock_validate_log.return_value = Path("/tmp/test.log")

        controller = Mock()
        mock_controller_class.return_value = controller

        # Run main
        main()

        # Verify calls
        mock_parse_args.assert_called_once()
        mock_config_load.assert_called_once_with(args)
        # config validation happens in main, not here
        mock_validate_log.assert_called_once()
        mock_setup_logging.assert_called_once_with(config)
        mock_controller_class.assert_called_once_with(config)
        controller.run.assert_called_once()

    @patch("mic_control.__main__.parse_args")
    @patch("mic_control.__main__.Config.load")
    def test_main_save_config(self, mock_config_load, mock_parse_args):
        """Test main with --save-config flag."""
        args = Mock(save_config=True)
        mock_parse_args.return_value = args

        config = Mock()
        mock_config_load.return_value = config

        main()

        config.save.assert_called_once()

    @patch("mic_control.__main__.sys.exit")
    @patch("mic_control.__main__.print")
    @patch("mic_control.__main__.Config.load")
    @patch("mic_control.__main__.parse_args")
    def test_main_invalid_config(self, mock_parse_args, mock_config_load, mock_print, mock_exit):
        """Test main with invalid configuration."""
        args = Mock(debug=False, save_config=False)
        mock_parse_args.return_value = args

        config = Mock()
        config.validate.side_effect = ValueError("Invalid config")
        mock_config_load.return_value = config

        # Make sys.exit actually exit to prevent further execution
        mock_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            main()

        mock_print.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("mic_control.__main__.logging")
    @patch("mic_control.__main__.MicrophoneController")
    @patch("mic_control.__main__.setup_logging")
    @patch("mic_control.__main__.validate_log_path")
    @patch("mic_control.__main__.Config.load")
    @patch("mic_control.__main__.parse_args")
    def test_main_keyboard_interrupt(
        self,
        mock_parse_args,
        mock_config_load,
        mock_validate_log,
        mock_setup_logging,
        mock_controller_class,
        mock_logging,
    ):
        """Test main with KeyboardInterrupt."""
        args = Mock(debug=False, save_config=False)
        mock_parse_args.return_value = args

        config = Config()
        mock_config_load.return_value = config
        mock_validate_log.return_value = Path("/tmp/test.log")

        controller = Mock()
        controller.run.side_effect = KeyboardInterrupt()
        mock_controller_class.return_value = controller

        main()

        mock_logging.info.assert_any_call("Interrupted by user")
