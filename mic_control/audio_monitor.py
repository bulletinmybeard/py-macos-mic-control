import logging
import time
from typing import List, Optional

import numpy as np
import sounddevice as sd


class AudioMonitor:
    """Monitors audio input and detects call activity."""

    DEFAULT_THRESHOLD = 0.01
    DEFAULT_SAMPLE_DURATION = 1.0
    DEFAULT_CALL_DETECTION_DURATION = 5
    DEFAULT_CALL_ACTIVITY_RATIO = 0.4

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        sample_duration: float = DEFAULT_SAMPLE_DURATION,
        call_detection_duration: int = DEFAULT_CALL_DETECTION_DURATION,
        call_activity_ratio: float = DEFAULT_CALL_ACTIVITY_RATIO,
    ):
        """Initialize the audio monitor."""
        self.threshold = threshold
        self.sample_duration = sample_duration
        self.call_detection_duration = call_detection_duration
        self.call_activity_ratio = call_activity_ratio
        self._device_info: Optional[dict] = None
        self._sample_rate: Optional[int] = None

    def _initialize_device(self) -> None:
        """Initialize audio device information."""
        if self._device_info is None:
            try:
                self._device_info = sd.query_devices(kind="input")
                self._sample_rate = int(self._device_info["default_samplerate"])
                logging.debug(f"Initialized audio device: {self._device_info['name']}")
            except Exception as e:
                logging.error(f"Failed to initialize audio device: {e}")
                raise

    def is_audio_active(self) -> bool:
        """Check if there's significant audio activity on the microphone."""
        try:
            self._initialize_device()

            if self._sample_rate is None:
                logging.error("Sample rate not initialized")
                return False

            # Record audio for specified duration
            samples = int(self.sample_duration * self._sample_rate)
            recording = sd.rec(
                samples,
                channels=1,
                dtype="float32",
                samplerate=self._sample_rate,
            )
            sd.wait()

            # Calculate RMS value
            rms = np.sqrt(np.mean(recording**2))

            is_active = rms > self.threshold
            logging.debug(f"Audio RMS: {rms:.4f}, Active: {is_active}")

            return bool(is_active)

        except Exception as e:
            logging.error(f"Error detecting audio: {e}")
            return False

    def detect_call_activity(self) -> bool:
        """Detect if we're likely in a call by monitoring audio activity over time."""
        audio_samples: List[bool] = []

        logging.debug(
            f"Starting call detection: {self.call_detection_duration} samples, "
            f"threshold ratio: {self.call_activity_ratio}"
        )

        # Take several samples over a period
        for i in range(self.call_detection_duration):
            is_active = self.is_audio_active()
            audio_samples.append(is_active)

            # Don't sleep after the last sample
            if i < self.call_detection_duration - 1:
                time.sleep(1)

        # Calculate activity ratio
        activity_ratio = sum(audio_samples) / len(audio_samples)
        in_call = activity_ratio >= self.call_activity_ratio

        logging.debug(
            f"Call detection complete: {sum(audio_samples)}/{len(audio_samples)} "
            f"active samples (ratio: {activity_ratio:.2f}), In call: {in_call}"
        )

        return in_call

    def cleanup(self) -> None:
        """Clean up audio resources."""
        # Currently no persistent resources to clean up
        # This method is here for future expansion
        pass
