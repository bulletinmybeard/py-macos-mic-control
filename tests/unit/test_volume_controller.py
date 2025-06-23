import subprocess
from unittest.mock import Mock, patch

import pytest

from mic_control.volume_controller import (
    MacOSVolumeController,
    VolumeController,
    get_volume_controller,
)


class TestMacOSVolumeController:
    """Test cases for MacOSVolumeController."""

    @pytest.fixture
    def controller(self):
        """Create a MacOSVolumeController instance."""
        return MacOSVolumeController()

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess.run."""
        with patch("mic_control.volume_controller.subprocess.run") as mock_run:
            yield mock_run

    def test_get_volume_success(self, controller, mock_subprocess):
        """Test successful volume retrieval."""
        mock_subprocess.return_value = Mock(
            stdout="75\n",
            returncode=0,
        )

        volume = controller.get_volume()

        assert volume == 75
        mock_subprocess.assert_called_once_with(
            ["/usr/bin/osascript", "-e", "input volume of (get volume settings)"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

    def test_get_volume_with_retry(self, controller, mock_subprocess):
        """Test volume retrieval with retry on failure."""
        # First call fails, second succeeds
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "osascript"),
            Mock(stdout="80\n", returncode=0),
        ]

        volume = controller.get_volume()

        assert volume == 80
        assert mock_subprocess.call_count == 2

    def test_get_volume_timeout_retry(self, controller, mock_subprocess):
        """Test volume retrieval with timeout and retry."""
        # First call times out, second succeeds
        mock_subprocess.side_effect = [
            subprocess.TimeoutExpired("osascript", 5),
            Mock(stdout="50\n", returncode=0),
        ]

        volume = controller.get_volume()

        assert volume == 50
        assert mock_subprocess.call_count == 2

    def test_get_volume_all_retries_fail(self, controller, mock_subprocess):
        """Test volume retrieval when all retries fail."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "osascript")

        volume = controller.get_volume()

        assert volume is None
        assert mock_subprocess.call_count == 3  # MAX_RETRIES

    def test_get_volume_cached_fallback(self, controller, mock_subprocess):
        """Test fallback to cached volume when retrieval fails."""
        # First call succeeds
        mock_subprocess.return_value = Mock(stdout="60\n", returncode=0)
        volume1 = controller.get_volume()
        assert volume1 == 60

        # Second call fails but returns cached value
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "osascript")
        volume2 = controller.get_volume()
        assert volume2 == 60

    def test_get_volume_parse_error(self, controller, mock_subprocess):
        """Test handling of parse errors."""
        mock_subprocess.return_value = Mock(stdout="invalid\n", returncode=0)

        volume = controller.get_volume()

        assert volume is None

    def test_set_volume_success(self, controller, mock_subprocess):
        """Test successful volume setting."""
        mock_subprocess.return_value = Mock(returncode=0)

        # Mock get_volume for verification
        with patch.object(controller, "get_volume", return_value=80):
            result = controller.set_volume(80)

        assert result is True
        mock_subprocess.assert_called_with(
            ["/usr/bin/osascript", "-e", "set volume input volume 80"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

    def test_set_volume_invalid_range(self, controller, mock_subprocess):
        """Test setting volume with invalid values."""
        assert controller.set_volume(-10) is False
        assert controller.set_volume(101) is False
        mock_subprocess.assert_not_called()

    def test_set_volume_with_retry(self, controller, mock_subprocess):
        """Test volume setting with retry on failure."""
        # First call fails, second succeeds
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "osascript"),
            Mock(returncode=0),
        ]

        with patch.object(controller, "get_volume", return_value=75):
            result = controller.set_volume(75)

        assert result is True
        assert mock_subprocess.call_count == 2

    def test_set_volume_all_retries_fail(self, controller, mock_subprocess):
        """Test volume setting when all retries fail."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "osascript")

        result = controller.set_volume(50)

        assert result is False
        assert mock_subprocess.call_count == 3  # MAX_RETRIES

    def test_set_volume_verification_warning(self, controller, mock_subprocess):
        """Test warning when set volume doesn't match actual."""
        mock_subprocess.return_value = Mock(returncode=0)

        # Mock get_volume to return different value
        with patch.object(controller, "get_volume", return_value=79):
            result = controller.set_volume(80)

        assert result is True  # Still returns True but logs warning

    @patch("mic_control.volume_controller.time.sleep")
    def test_retry_delay(self, mock_sleep, controller, mock_subprocess):
        """Test that retry delay is applied between attempts."""
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "osascript"),
            subprocess.CalledProcessError(1, "osascript"),
            Mock(stdout="50\n", returncode=0),
        ]

        controller.get_volume()

        # sleep should be called twice (before 2nd and 3rd attempts)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)  # RETRY_DELAY


class TestVolumeControllerFactory:
    """Test the factory function."""

    def test_get_volume_controller_returns_macos(self):
        """Test that factory returns MacOSVolumeController."""
        controller = get_volume_controller()
        assert isinstance(controller, MacOSVolumeController)

    def test_volume_controller_is_abstract(self):
        """Test that VolumeController cannot be instantiated."""
        with pytest.raises(TypeError):
            VolumeController()
