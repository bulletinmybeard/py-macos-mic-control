import os
import sys
from pathlib import Path


def validate_log_path(log_path: str) -> Path:
    """Validate the log file path and ensure it's usable."""
    try:
        # Convert to Path object and resolve any relative paths
        log_path = Path(log_path).resolve()

        # Check if parent directory exists, if not try to create it
        if not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                sys.exit(f"Error: No permission to create directory: {log_path.parent}")
            except OSError as e:
                sys.exit(f"Error: Could not create directory {log_path.parent}: {e}")

        # Check if parent directory is actually a directory
        if not log_path.parent.is_dir():
            sys.exit(f"Error: {log_path.parent} exists but is not a directory")

        # Check directory permissions
        if not os.access(log_path.parent, os.R_OK | os.W_OK | os.X_OK):
            sys.exit(f"Error: Insufficient permissions for directory: {log_path.parent}")

        # If log file exists, check if it's a regular file and writable
        if log_path.exists():
            if not log_path.is_file():
                sys.exit(f"Error: {log_path} exists but is not a regular file")
            if not os.access(log_path, os.W_OK):
                sys.exit(f"Error: No write permission for existing log file: {log_path}")
        else:
            # Check if we can create the file by trying to open it
            try:
                with open(log_path, "a"):
                    pass
                log_path.unlink()  # Remove the test file
            except PermissionError:
                sys.exit(f"Error: No permission to create log file: {log_path}")
            except OSError as e:
                sys.exit(f"Error: Could not create log file {log_path}: {e}")

        return log_path

    except Exception as e:
        sys.exit(f"Error: Invalid log path {log_path}: {e}")
        return None
