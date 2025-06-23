import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Volume settings
    target_volume: int = 80

    # Timing intervals (in seconds)
    active_interval: int = 3
    idle_interval: int = 15
    call_interval: int = 30

    # Audio detection settings
    audio_threshold: float = 0.01
    sample_duration: float = 1.0
    call_detection_duration: int = 5
    call_activity_ratio: float = 0.4

    # Logging
    log_path: Path = Path("mic_control.log")
    log_level: str = "INFO"

    # Advanced settings
    max_retries: int = 3
    retry_delay: float = 0.5

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        """Create config from command line arguments."""
        return cls(
            target_volume=args.target_volume,
            active_interval=args.active_interval,
            idle_interval=args.idle_interval,
            call_interval=args.call_interval,
            log_path=Path(args.log_path),
        )

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load config from JSON file."""
        with open(config_path, "r") as f:
            data = json.load(f)

        # Convert log_path to Path object if present
        if "log_path" in data:
            data["log_path"] = Path(data["log_path"])

        return cls(**data)

    @classmethod
    def load(cls, args: Optional[argparse.Namespace] = None) -> "Config":
        """
        Load configuration from file or arguments.

        Looks for config in the following order:
        1. Command line arguments (if provided)
        2. Config file specified in args
        3. ~/.mic_control/config.json
        4. Default values
        """
        # Start with default config
        config = cls()

        # Check for config file in home directory
        home_config = Path.home() / ".mic_control" / "config.json"
        if home_config.exists():
            try:
                config = cls.from_file(home_config)
            except Exception as e:
                # Log error but continue with defaults
                print(f"Error loading config from {home_config}: {e}")

        # Override with command line arguments if provided
        if args:
            # Update only the values that were explicitly provided
            if hasattr(args, "target_volume") and args.target_volume is not None:
                config.target_volume = args.target_volume
            if hasattr(args, "active_interval") and args.active_interval is not None:
                config.active_interval = args.active_interval
            if hasattr(args, "idle_interval") and args.idle_interval is not None:
                config.idle_interval = args.idle_interval
            if hasattr(args, "call_interval") and args.call_interval is not None:
                config.call_interval = args.call_interval
            if hasattr(args, "log_path") and args.log_path is not None:
                config.log_path = Path(args.log_path)

        return config

    def save(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".mic_control" / "config.json"

        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = {
            "target_volume": self.target_volume,
            "active_interval": self.active_interval,
            "idle_interval": self.idle_interval,
            "call_interval": self.call_interval,
            "audio_threshold": self.audio_threshold,
            "sample_duration": self.sample_duration,
            "call_detection_duration": self.call_detection_duration,
            "call_activity_ratio": self.call_activity_ratio,
            "log_path": str(self.log_path),
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    def validate(self) -> None:
        """Validate configuration values."""
        if not 0 <= self.target_volume <= 100:
            raise ValueError(f"target_volume must be between 0 and 100, got {self.target_volume}")

        if self.active_interval <= 0:
            raise ValueError(f"active_interval must be positive, got {self.active_interval}")

        if self.idle_interval <= 0:
            raise ValueError(f"idle_interval must be positive, got {self.idle_interval}")

        if self.call_interval <= 0:
            raise ValueError(f"call_interval must be positive, got {self.call_interval}")

        if self.audio_threshold <= 0:
            raise ValueError(f"audio_threshold must be positive, got {self.audio_threshold}")

        if self.sample_duration <= 0:
            raise ValueError(f"sample_duration must be positive, got {self.sample_duration}")

        if self.call_detection_duration <= 0:
            raise ValueError(
                f"call_detection_duration must be positive, got {self.call_detection_duration}"
            )

        if not 0 <= self.call_activity_ratio <= 1:
            raise ValueError(
                f"call_activity_ratio must be between 0 and 1, got {self.call_activity_ratio}"
            )
