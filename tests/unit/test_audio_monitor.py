from unittest.mock import patch

import numpy as np
import pytest

from mic_control.audio_monitor import AudioMonitor


@pytest.fixture
def audio_monitor():
    """Create an AudioMonitor instance for testing."""
    return AudioMonitor()


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice module."""
    with patch("mic_control.audio_monitor.sd") as mock_sd:
        # Mock device info
        mock_sd.query_devices.return_value = {
            "name": "Test Microphone",
            "default_samplerate": 44100.0,
        }
        yield mock_sd


class TestAudioMonitor:
    """Test cases for AudioMonitor class."""

    def test_initialization_default_values(self):
        """Test AudioMonitor initialization with default values."""
        monitor = AudioMonitor()
        assert monitor.threshold == AudioMonitor.DEFAULT_THRESHOLD
        assert monitor.sample_duration == AudioMonitor.DEFAULT_SAMPLE_DURATION
        assert monitor.call_detection_duration == AudioMonitor.DEFAULT_CALL_DETECTION_DURATION
        assert monitor.call_activity_ratio == AudioMonitor.DEFAULT_CALL_ACTIVITY_RATIO

    def test_initialization_custom_values(self):
        """Test AudioMonitor initialization with custom values."""
        monitor = AudioMonitor(
            threshold=0.02,
            sample_duration=2.0,
            call_detection_duration=10,
            call_activity_ratio=0.5,
        )
        assert monitor.threshold == 0.02
        assert monitor.sample_duration == 2.0
        assert monitor.call_detection_duration == 10
        assert monitor.call_activity_ratio == 0.5

    def test_is_audio_active_true(self, audio_monitor, mock_sounddevice):
        """Test audio detection when activity is above threshold."""
        # Create audio data with RMS above threshold
        audio_data = np.random.normal(0, 0.05, size=(44100, 1)).astype(np.float32)
        mock_sounddevice.rec.return_value = audio_data

        result = audio_monitor.is_audio_active()

        assert result is True
        mock_sounddevice.query_devices.assert_called_once_with(kind="input")
        mock_sounddevice.rec.assert_called_once()
        mock_sounddevice.wait.assert_called_once()

    def test_is_audio_active_false(self, audio_monitor, mock_sounddevice):
        """Test audio detection when activity is below threshold."""
        # Create quiet audio data
        audio_data = np.zeros((44100, 1), dtype=np.float32)
        mock_sounddevice.rec.return_value = audio_data

        result = audio_monitor.is_audio_active()

        assert result is False

    def test_is_audio_active_device_error(self, audio_monitor, mock_sounddevice):
        """Test audio detection when device initialization fails."""
        mock_sounddevice.query_devices.side_effect = Exception("Device not found")

        result = audio_monitor.is_audio_active()

        assert result is False

    def test_is_audio_active_recording_error(self, audio_monitor, mock_sounddevice):
        """Test audio detection when recording fails."""
        mock_sounddevice.rec.side_effect = Exception("Recording failed")

        result = audio_monitor.is_audio_active()

        assert result is False

    @patch("mic_control.audio_monitor.time.sleep")
    def test_detect_call_activity_active(self, mock_sleep, audio_monitor):
        """Test call detection when sufficient activity is detected."""
        # Mock is_audio_active to return True for 3 out of 5 samples (60%)
        with patch.object(
            audio_monitor, "is_audio_active", side_effect=[True, False, True, False, True]
        ):
            result = audio_monitor.detect_call_activity()

        assert result is True
        assert mock_sleep.call_count == 4  # Called 4 times (not after last sample)

    @patch("mic_control.audio_monitor.time.sleep")
    def test_detect_call_activity_inactive(self, mock_sleep, audio_monitor):
        """Test call detection when insufficient activity is detected."""
        # Mock is_audio_active to return True for only 1 out of 5 samples (20%)
        with patch.object(
            audio_monitor, "is_audio_active", side_effect=[False, False, True, False, False]
        ):
            result = audio_monitor.detect_call_activity()

        assert result is False

    @patch("mic_control.audio_monitor.time.sleep")
    def test_detect_call_activity_custom_duration(self, mock_sleep):
        """Test call detection with custom duration."""
        monitor = AudioMonitor(call_detection_duration=3)

        with patch.object(monitor, "is_audio_active", side_effect=[True, True, False]):
            result = monitor.detect_call_activity()

        assert result is True  # 2/3 = 66.7% > 40%
        assert mock_sleep.call_count == 2

    @patch("mic_control.audio_monitor.time.sleep")
    def test_detect_call_activity_custom_ratio(self, mock_sleep):
        """Test call detection with custom activity ratio."""
        monitor = AudioMonitor(call_activity_ratio=0.8)

        # 3/5 = 60% < 80%
        with patch.object(monitor, "is_audio_active", side_effect=[True, True, True, False, False]):
            result = monitor.detect_call_activity()

        assert result is False

    def test_device_initialization_caching(self, audio_monitor, mock_sounddevice):
        """Test that device info is cached after first initialization."""
        audio_data = np.zeros((44100, 1), dtype=np.float32)
        mock_sounddevice.rec.return_value = audio_data

        # Call is_audio_active twice
        audio_monitor.is_audio_active()
        audio_monitor.is_audio_active()

        # Device should only be queried once
        assert mock_sounddevice.query_devices.call_count == 1

    def test_cleanup(self, audio_monitor):
        """Test cleanup method."""
        # Should not raise any exceptions
        audio_monitor.cleanup()
