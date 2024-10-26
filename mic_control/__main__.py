import argparse
import logging
import subprocess  # nosec B404
import sys
import time
from typing import Optional

import numpy as np
import sounddevice as sd

from mic_control.utils import validate_log_path


def set_mic_volume(
    volume,
) -> bool:
    """Set the microphone input volume (0-100)."""
    try:
        cmd = f"osascript -e 'set volume input volume {volume}'"
        subprocess.run(
            cmd,
            shell=True,  # nosec B602
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set volume: {e}")
        return False


def get_mic_volume() -> Optional[int]:
    """Get current microphone input volume."""
    try:
        cmd = "osascript -e 'input volume of (get volume settings)'"
        result = subprocess.run(
            cmd,
            shell=True,  # nosec B602
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get volume: {e}")
        return None


def is_audio_active(
    threshold=0.01,
    duration=1.0,
) -> bool:
    """Check if there's significant audio activity on the microphone."""
    try:
        # Get default input device
        device_info = sd.query_devices(kind="input")
        sample_rate = int(device_info["default_samplerate"])

        # Record audio for specified duration
        recording = sd.rec(
            int(duration * sample_rate),
            channels=1,
            dtype="float32",
            samplerate=sample_rate,
        )
        sd.wait()

        # Calculate RMS value
        rms = np.sqrt(np.mean(recording**2))

        return rms > threshold

    except Exception as e:
        logging.error(f"Error detecting audio: {e}")
        return False


def detect_call_activity(
    audio_check_duration=5,
) -> bool:
    """Detect if we're likely in a call by monitoring audio activity over time."""
    audio_samples = []

    # Take several samples over a period
    for _ in range(audio_check_duration):
        audio_samples.append(is_audio_active())
        time.sleep(1)

    # If we detect audio activity in at least 40% of samples,
    # we're probably in a call
    return sum(audio_samples) / len(audio_samples) >= 0.4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatic microphone volume control for macOS calls and meetings"
    )
    parser.add_argument(
        "--target-volume",
        type=int,
        default=80,
        help="Target microphone volume level (0-100)",
        choices=range(0, 101),
        metavar="VOLUME",
    )
    parser.add_argument(
        "--active-interval",
        type=int,
        default=3,
        help="Seconds between checks during calls (default: 3)",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--idle-interval",
        type=int,
        default=15,
        help="Seconds between checks when idle (default: 15)",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--call-interval",
        type=int,
        default=30,
        help="Seconds between full call detection checks (default: 30)",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="mic_control.log",
        help="Path to the log file (default: mic_control.log)",
        metavar="PATH",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    log_path = args.log_path

    # Validate log path before setting up logging
    try:
        log_path = validate_log_path(args.log_path)
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )

    # Log the configuration
    logging.info(
        f"Starting microphone level controller with settings:\n"
        f"- Target Volume: {args.target_volume}\n"
        f"- Active Check Interval: {args.active_interval}s\n"
        f"- Idle Check Interval: {args.idle_interval}s\n"
        f"- Call Check Interval: {args.call_interval}s\n"
        f"- Log Path: {log_path}"
    )

    last_call_check = 0
    in_call = False

    while True:
        current_time = time.time()

        # Periodically do a full call detection check
        if current_time - last_call_check > args.call_interval:
            in_call = detect_call_activity()
            last_call_check = current_time
            logging.info(f"Call status check: {'in call' if in_call else 'not in call'}")

        if in_call:
            current_volume = get_mic_volume()

            if current_volume is not None and current_volume != args.target_volume:
                logging.info(
                    f"In call: Adjusting volume from {current_volume} to {args.target_volume}"
                )
                set_mic_volume(args.target_volume)

            time.sleep(args.active_interval)
        else:
            time.sleep(args.idle_interval)


if __name__ == "__main__":
    main()
