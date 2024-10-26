import subprocess
from unittest.mock import Mock, patch

import numpy as np
import pytest

from mic_control.__main__ import (
    detect_call_activity,
    get_mic_volume,
    is_audio_active,
    set_mic_volume,
)


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_sounddevice():
    with patch("sounddevice.query_devices") as mock_query:
        with patch("sounddevice.rec") as mock_rec:
            with patch("sounddevice.wait") as mock_wait:
                mock_query.return_value = {"default_samplerate": 44100}
                yield mock_query, mock_rec, mock_wait


def test_set_mic_volume_success(mock_subprocess):
    mock_subprocess.return_value = Mock(returncode=0)
    assert set_mic_volume(50) is True
    mock_subprocess.assert_called_once_with(
        "osascript -e 'set volume input volume 50'",
        shell=True,
        check=True,
    )


def test_set_mic_volume_failure(mock_subprocess):
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert set_mic_volume(50) is False


def test_get_mic_volume_success(mock_subprocess):
    mock_subprocess.return_value = Mock(
        returncode=0,
        stdout="75\n",
    )
    assert get_mic_volume() == 75
    mock_subprocess.assert_called_once_with(
        "osascript -e 'input volume of (get volume settings)'",
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )


def test_get_mic_volume_failure(mock_subprocess):
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert get_mic_volume() is None


def test_is_audio_active_success(mock_sounddevice):
    _, mock_rec, _ = mock_sounddevice
    # Simulate audio recording with values that will produce RMS > threshold
    mock_rec.return_value = np.array([[0.1], [0.2], [0.3]])

    assert is_audio_active(threshold=0.01, duration=1.0)


def test_is_audio_active_no_sound(mock_sounddevice):
    _, mock_rec, _ = mock_sounddevice
    # Simulate audio recording with values that will produce RMS < threshold
    mock_rec.return_value = np.array([[0.001], [0.002], [0.001]])

    assert not is_audio_active(threshold=0.01, duration=1.0)


def test_is_audio_active_error(mock_sounddevice):
    mock_query, _, _ = mock_sounddevice
    mock_query.side_effect = Exception("Device error")

    assert not is_audio_active()


@patch("mic_control.__main__.is_audio_active")
@patch("mic_control.__main__.time.sleep")
def test_detect_call_activity_active(mock_sleep, mock_is_audio_active):
    # Simulate 3 out of 5 samples being active (60% > 40% threshold)
    mock_is_audio_active.side_effect = [True, True, True, False, False]

    assert detect_call_activity(audio_check_duration=5) is True
    assert mock_is_audio_active.call_count == 5
    assert mock_sleep.call_count == 5


@patch("mic_control.__main__.is_audio_active")
@patch("mic_control.__main__.time.sleep")
def test_detect_call_activity_inactive(mock_sleep, mock_is_audio_active):
    # Simulate 1 out of 5 samples being active (20% < 40% threshold)
    mock_is_audio_active.side_effect = [True, False, False, False, False]

    assert detect_call_activity(audio_check_duration=5) is False
    assert mock_is_audio_active.call_count == 5
    assert mock_sleep.call_count == 5


@pytest.mark.parametrize(
    "volume,expected",
    [
        (0, True),
        (50, True),
        (100, True),
        (-1, False),  # Invalid volume
        (101, False),  # Invalid volume
    ],
)
def test_set_mic_volume_boundaries(mock_subprocess, volume, expected):
    if not expected:
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
    assert set_mic_volume(volume) is expected
