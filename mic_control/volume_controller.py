import logging
import subprocess  # nosec B404
import time
from abc import ABC, abstractmethod
from typing import Optional


class VolumeController(ABC):
    """Abstract base class for volume control implementations."""

    @abstractmethod
    def get_volume(self) -> Optional[int]:
        """Get current microphone input volume."""
        pass

    @abstractmethod
    def set_volume(self, volume: int) -> bool:
        """Set microphone input volume."""
        pass


class MacOSVolumeController(VolumeController):
    """macOS implementation using osascript."""

    MAX_RETRIES = 3
    RETRY_DELAY = 0.5

    def __init__(self):
        """Initialize the macOS volume controller."""
        self._last_known_volume: Optional[int] = None

    def _execute_osascript(self, script: str) -> subprocess.CompletedProcess:
        """Execute an osascript command with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                result = subprocess.run(  # nosec B603
                    ["/usr/bin/osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=5,  # 5 second timeout
                )
                return result
            except subprocess.TimeoutExpired:
                logging.warning(f"osascript timeout on attempt {attempt + 1}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise
            except subprocess.CalledProcessError as e:
                if attempt < self.MAX_RETRIES - 1:
                    logging.warning(f"osascript failed on attempt {attempt + 1}: {e}")
                    time.sleep(self.RETRY_DELAY)
                else:
                    raise

    def get_volume(self) -> Optional[int]:
        """Get current microphone input volume."""
        try:
            script = "input volume of (get volume settings)"
            result = self._execute_osascript(script)
            volume = int(result.stdout.strip())

            # Cache the last known volume
            self._last_known_volume = volume

            return volume

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f"Failed to get volume: {e}")
            # Return cached value if available
            if self._last_known_volume is not None:
                logging.info(f"Using cached volume: {self._last_known_volume}")
                return self._last_known_volume
            return None
        except (ValueError, AttributeError) as e:
            logging.error(f"Failed to parse volume output: {e}")
            return None

    def set_volume(self, volume: int) -> bool:
        """Set microphone input volume."""
        # Validate input
        if not 0 <= volume <= 100:
            logging.error(f"Invalid volume level: {volume}")
            return False

        try:
            script = f"set volume input volume {volume}"
            self._execute_osascript(script)

            # Update cached volume
            self._last_known_volume = volume

            # Verify the change
            actual_volume = self.get_volume()
            if actual_volume is not None and actual_volume != volume:
                logging.warning(f"Volume set to {volume} but actual volume is {actual_volume}")

            return True

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logging.error(f"Failed to set volume: {e}")
            return False


def get_volume_controller() -> VolumeController:
    """Factory function to get the appropriate volume controller for the platform."""
    # For now, we only support macOS
    # Future implementations could detect the platform and return appropriate controller
    return MacOSVolumeController()
