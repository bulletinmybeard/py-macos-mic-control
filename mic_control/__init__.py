"""Automatic microphone volume control for macOS calls and meetings."""

from mic_control.audio_monitor import AudioMonitor
from mic_control.config import Config
from mic_control.volume_controller import (
    MacOSVolumeController,
    VolumeController,
    get_volume_controller,
)

__version__ = "0.5.0"
__all__ = [
    "AudioMonitor",
    "Config",
    "VolumeController",
    "MacOSVolumeController",
    "get_volume_controller",
]
