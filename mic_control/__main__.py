import argparse
import logging
import signal
import sys
import time
from pathlib import Path

from mic_control.audio_monitor import AudioMonitor
from mic_control.config import Config
from mic_control.utils import validate_log_path
from mic_control.volume_controller import get_volume_controller


class MicrophoneController:
    """Main controller for microphone volume management."""

    def __init__(self, config: Config):
        """Initialize the microphone controller."""
        self.config = config
        self.audio_monitor = AudioMonitor(
            threshold=config.audio_threshold,
            sample_duration=config.sample_duration,
            call_detection_duration=config.call_detection_duration,
            call_activity_ratio=config.call_activity_ratio,
        )
        self.volume_controller = get_volume_controller()
        self.running = True
        self.in_call = False
        self.last_call_check = 0.0

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run(self) -> None:
        """Run the main control loop."""
        logging.info(
            f"Starting microphone level controller with settings:\n"
            f"- Target Volume: {self.config.target_volume}\n"
            f"- Active Check Interval: {self.config.active_interval}s\n"
            f"- Idle Check Interval: {self.config.idle_interval}s\n"
            f"- Call Check Interval: {self.config.call_interval}s\n"
            f"- Log Path: {self.config.log_path}"
        )

        try:
            while self.running:
                current_time = time.time()

                # Periodically do a full call detection check
                if current_time - self.last_call_check > self.config.call_interval:
                    self.in_call = self.audio_monitor.detect_call_activity()
                    self.last_call_check = current_time
                    logging.info(
                        f"Call status check: {'in call' if self.in_call else 'not in call'}"
                    )

                if self.in_call:
                    self._handle_active_call()
                    time.sleep(self.config.active_interval)
                else:
                    time.sleep(self.config.idle_interval)

        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}", exc_info=True)
            raise
        finally:
            self.cleanup()

    def _handle_active_call(self) -> None:
        """Handle volume adjustment during an active call."""
        current_volume = self.volume_controller.get_volume()

        if current_volume is not None and current_volume != self.config.target_volume:
            logging.info(
                f"In call: Adjusting volume from {current_volume} to {self.config.target_volume}"
            )
            success = self.volume_controller.set_volume(self.config.target_volume)
            if not success:
                logging.warning("Failed to adjust volume, will retry on next check")

    def cleanup(self) -> None:
        """Clean up resources."""
        logging.info("Cleaning up resources...")
        self.audio_monitor.cleanup()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automatic microphone volume control for macOS calls and meetings"
    )
    parser.add_argument(
        "--target-volume",
        type=int,
        help="Target microphone volume level (0-100)",
        choices=range(0, 101),
        metavar="VOLUME",
    )
    parser.add_argument(
        "--active-interval",
        type=int,
        help="Seconds between checks during calls",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--idle-interval",
        type=int,
        help="Seconds between checks when idle",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--call-interval",
        type=int,
        help="Seconds between full call detection checks",
        metavar="SECONDS",
    )
    parser.add_argument(
        "--log-path",
        type=str,
        help="Path to the log file",
        metavar="PATH",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        metavar="CONFIG_PATH",
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save current configuration to file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def setup_logging(config: Config) -> None:
    """Setup logging configuration."""
    log_level = logging.DEBUG if config.log_level == "DEBUG" else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.log_path),
            logging.StreamHandler(),
        ],
    )

    # Set library log levels
    logging.getLogger("sounddevice").setLevel(logging.WARNING)


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load configuration
    config = Config.load(args)

    # Override with debug flag if provided
    if args.debug:
        config.log_level = "DEBUG"

    # Save config if requested
    if args.save_config:
        config.save()
        print(f"Configuration saved to {Path.home() / '.mic_control' / 'config.json'}")
        return

    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        print(f"Invalid configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate log path
    try:
        config.log_path = validate_log_path(str(config.log_path))
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Setup logging
    setup_logging(config)

    # Create and run controller
    controller = MicrophoneController(config)

    try:
        controller.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("Microphone controller stopped")


if __name__ == "__main__":
    main()
