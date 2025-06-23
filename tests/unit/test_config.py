import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from mic_control.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_default_values(self):
        """Test Config with default values."""
        config = Config()

        assert config.target_volume == 80
        assert config.active_interval == 3
        assert config.idle_interval == 15
        assert config.call_interval == 30
        assert config.audio_threshold == 0.01
        assert config.sample_duration == 1.0
        assert config.call_detection_duration == 5
        assert config.call_activity_ratio == 0.4
        assert config.log_path == Path("mic_control.log")
        assert config.log_level == "INFO"
        assert config.max_retries == 3
        assert config.retry_delay == 0.5

    def test_from_args(self):
        """Test creating Config from command line arguments."""
        args = argparse.Namespace(
            target_volume=75,
            active_interval=5,
            idle_interval=20,
            call_interval=45,
            log_path="/tmp/test.log",
        )

        config = Config.from_args(args)

        assert config.target_volume == 75
        assert config.active_interval == 5
        assert config.idle_interval == 20
        assert config.call_interval == 45
        assert config.log_path == Path("/tmp/test.log")

    def test_from_file(self):
        """Test loading Config from JSON file."""
        config_data = {
            "target_volume": 70,
            "active_interval": 4,
            "idle_interval": 18,
            "call_interval": 35,
            "audio_threshold": 0.02,
            "sample_duration": 1.5,
            "call_detection_duration": 6,
            "call_activity_ratio": 0.5,
            "log_path": "/var/log/mic.log",
            "log_level": "DEBUG",
            "max_retries": 5,
            "retry_delay": 1.0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            config = Config.from_file(temp_path)

            assert config.target_volume == 70
            assert config.active_interval == 4
            assert config.idle_interval == 18
            assert config.call_interval == 35
            assert config.audio_threshold == 0.02
            assert config.sample_duration == 1.5
            assert config.call_detection_duration == 6
            assert config.call_activity_ratio == 0.5
            assert config.log_path == Path("/var/log/mic.log")
            assert config.log_level == "DEBUG"
            assert config.max_retries == 5
            assert config.retry_delay == 1.0
        finally:
            temp_path.unlink()

    @patch("mic_control.config.Path.home")
    @patch("mic_control.config.Path.exists")
    def test_load_no_config_file(self, mock_exists, mock_home):
        """Test loading when no config file exists."""
        mock_home.return_value = Path("/home/user")
        mock_exists.return_value = False

        config = Config.load()

        # Should return default config
        assert config.target_volume == 80
        assert config.active_interval == 3

    @patch("mic_control.config.Path.home")
    def test_load_with_home_config(self, mock_home):
        """Test loading with config file in home directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_home.return_value = temp_path

            # Create config directory and file
            config_dir = temp_path / ".mic_control"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            config_data = {"target_volume": 65}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            config = Config.load()

            assert config.target_volume == 65

    def test_load_with_args_override(self):
        """Test that command line args override config file."""
        args = Mock(
            target_volume=90,
            active_interval=None,  # Not provided
            idle_interval=25,
            call_interval=None,
            log_path="/tmp/override.log",
        )

        config = Config.load(args)

        assert config.target_volume == 90
        assert config.active_interval == 3  # Default
        assert config.idle_interval == 25
        assert config.call_interval == 30  # Default
        assert config.log_path == Path("/tmp/override.log")

    def test_save(self):
        """Test saving configuration to file."""
        config = Config(
            target_volume=85,
            log_path=Path("/tmp/test.log"),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            config.save(temp_path)

            # Load and verify
            with open(temp_path, "r") as f:
                data = json.load(f)

            assert data["target_volume"] == 85
            assert data["log_path"] == "/tmp/test.log"
            assert "active_interval" in data
            assert "idle_interval" in data
        finally:
            temp_path.unlink()

    @patch("mic_control.config.Path.home")
    def test_save_default_location(self, mock_home):
        """Test saving to default location."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_home.return_value = temp_path

            config = Config()
            config.save()

            config_file = temp_path / ".mic_control" / "config.json"
            assert config_file.exists()

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = Config()
        config.validate()  # Should not raise

    def test_validate_invalid_target_volume(self):
        """Test validation with invalid target volume."""
        config = Config(target_volume=150)

        with pytest.raises(ValueError, match="target_volume must be between 0 and 100"):
            config.validate()

    def test_validate_negative_intervals(self):
        """Test validation with negative intervals."""
        config = Config(active_interval=-1)

        with pytest.raises(ValueError, match="active_interval must be positive"):
            config.validate()

    def test_validate_invalid_audio_threshold(self):
        """Test validation with invalid audio threshold."""
        config = Config(audio_threshold=0)

        with pytest.raises(ValueError, match="audio_threshold must be positive"):
            config.validate()

    def test_validate_invalid_call_activity_ratio(self):
        """Test validation with invalid call activity ratio."""
        config = Config(call_activity_ratio=1.5)

        with pytest.raises(ValueError, match="call_activity_ratio must be between 0 and 1"):
            config.validate()

    @patch("mic_control.config.print")
    @patch("mic_control.config.Path.exists")
    def test_load_corrupted_config(self, mock_exists, mock_print):
        """Test loading with corrupted config file."""
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data="invalid json")):
            config = Config.load()

        # Should print error and return default config
        mock_print.assert_called_once()
        assert config.target_volume == 80  # Default value
