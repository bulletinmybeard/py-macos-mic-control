import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mic_control.utils import validate_log_path


class TestValidateLogPath:
    """Test cases for validate_log_path function."""

    def test_valid_existing_file(self):
        """Test with a valid existing log file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = validate_log_path(str(temp_path))
            assert result == temp_path.resolve()
        finally:
            temp_path.unlink()

    def test_valid_new_file_in_existing_directory(self):
        """Test creating a new log file in an existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "new_log.log"

            result = validate_log_path(str(log_path))
            assert result == log_path.resolve()

    def test_create_parent_directory(self):
        """Test creating parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "subdir" / "log.log"

            result = validate_log_path(str(log_path))
            assert result == log_path.resolve()
            assert log_path.parent.exists()

    def test_relative_path_resolution(self):
        """Test that relative paths are resolved to absolute."""
        result = validate_log_path("./test.log")
        assert result.is_absolute()

    def test_no_permission_to_create_directory(self):
        """Test handling of permission error when creating directory."""
        with patch("mic_control.utils.Path") as mock_path_class:
            mock_path = Mock()
            mock_parent = Mock()
            mock_parent.exists.return_value = False
            mock_parent.mkdir.side_effect = PermissionError("No permission")
            mock_path.parent = mock_parent
            mock_path.resolve.return_value = mock_path
            mock_path_class.return_value = mock_path

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path("/restricted/log.log")

            assert "No permission to create directory" in str(exc_info.value)

    def test_os_error_creating_directory(self):
        """Test handling of OS error when creating directory."""
        with patch("mic_control.utils.Path") as mock_path_class:
            mock_path = Mock()
            mock_parent = Mock()
            mock_parent.exists.return_value = False
            mock_parent.mkdir.side_effect = OSError("Disk full")
            mock_path.parent = mock_parent
            mock_path.resolve.return_value = mock_path
            mock_path_class.return_value = mock_path

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path("/invalid/log.log")

            assert "Could not create directory" in str(exc_info.value)

    def test_parent_is_file_not_directory(self):
        """Test when parent path exists but is a file, not directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = Path(f.name)

        try:
            log_path = str(temp_file) + "/log.log"  # Parent is a file

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(log_path)

            assert "exists but is not a directory" in str(exc_info.value)
        finally:
            temp_file.unlink()

    @patch("mic_control.utils.os.access")
    def test_insufficient_directory_permissions(self, mock_access):
        """Test when directory exists but lacks permissions."""
        mock_access.return_value = False

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(temp_dir + "/log.log")

            assert "Insufficient permissions for directory" in str(exc_info.value)

    def test_existing_log_not_regular_file(self):
        """Test when log path exists but is not a regular file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use the directory itself as the log path
            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(temp_dir)

            assert "exists but is not a regular file" in str(exc_info.value)

    @patch("mic_control.utils.os.access")
    def test_no_write_permission_existing_file(self, mock_access):
        """Test when existing log file lacks write permission."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)

        try:
            # First call returns True (directory check), second returns False (file check)
            mock_access.side_effect = [True, False]

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(str(temp_path))

            assert "No write permission for existing log file" in str(exc_info.value)
        finally:
            temp_path.unlink()

    @patch("builtins.open")
    def test_permission_error_creating_file(self, mock_open):
        """Test handling of permission error when creating new file."""
        mock_open.side_effect = PermissionError("No permission")

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(str(log_path))

            assert "No permission to create log file" in str(exc_info.value)

    @patch("builtins.open")
    def test_os_error_creating_file(self, mock_open):
        """Test handling of OS error when creating new file."""
        mock_open.side_effect = OSError("Disk full")

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"

            with pytest.raises(SystemExit) as exc_info:
                validate_log_path(str(log_path))

            assert "Could not create log file" in str(exc_info.value)

    def test_cleanup_test_file(self):
        """Test that test file is cleaned up after validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"

            # File shouldn't exist before
            assert not log_path.exists()

            validate_log_path(str(log_path))

            # File shouldn't exist after (test file was cleaned up)
            assert not log_path.exists()

    @patch("mic_control.utils.Path.resolve")
    def test_general_exception_handling(self, mock_resolve):
        """Test handling of unexpected exceptions."""
        mock_resolve.side_effect = Exception("Unexpected error")

        with pytest.raises(SystemExit) as exc_info:
            validate_log_path("test.log")

        assert "Invalid log path" in str(exc_info.value)
        assert "Unexpected error" in str(exc_info.value)
