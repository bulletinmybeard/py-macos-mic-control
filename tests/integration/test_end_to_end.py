import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mic_control.audio_monitor import AudioMonitor
from mic_control.config import Config
from mic_control.volume_controller import get_volume_controller


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.integration
    def test_audio_monitor_with_real_config(self):
        """Test AudioMonitor with configuration values."""
        config = Config(
            audio_threshold=0.02,
            sample_duration=0.5,
            call_detection_duration=3,
            call_activity_ratio=0.3,
        )
        
        audio_monitor = AudioMonitor(
            threshold=config.audio_threshold,
            sample_duration=config.sample_duration,
            call_detection_duration=config.call_detection_duration,
            call_activity_ratio=config.call_activity_ratio,
        )
        
        assert audio_monitor.threshold == 0.02
        assert audio_monitor.sample_duration == 0.5
        assert audio_monitor.call_detection_duration == 3
        assert audio_monitor.call_activity_ratio == 0.3

    @pytest.mark.integration
    def test_config_save_and_load_cycle(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            
            # Create and save config
            original_config = Config(
                target_volume=75,
                active_interval=5,
                idle_interval=20,
                call_interval=45,
                audio_threshold=0.015,
                log_path=Path("/tmp/test.log"),
            )
            original_config.save(config_path)
            
            # Load config
            loaded_config = Config.from_file(config_path)
            
            # Verify values match
            assert loaded_config.target_volume == original_config.target_volume
            assert loaded_config.active_interval == original_config.active_interval
            assert loaded_config.idle_interval == original_config.idle_interval
            assert loaded_config.call_interval == original_config.call_interval
            assert loaded_config.audio_threshold == original_config.audio_threshold
            assert loaded_config.log_path == original_config.log_path

    @pytest.mark.integration
    def test_volume_controller_factory(self):
        """Test volume controller factory returns correct implementation."""
        controller = get_volume_controller()
        
        # Should return MacOSVolumeController on macOS
        from mic_control.volume_controller import MacOSVolumeController
        assert isinstance(controller, MacOSVolumeController)
        
    @pytest.mark.integration
    @patch("mic_control.volume_controller.subprocess.run")
    def test_volume_controller_retry_mechanism(self, mock_run):
        """Test that volume controller properly retries on failure."""
        from mic_control.volume_controller import MacOSVolumeController
        
        controller = MacOSVolumeController()
        
        # First two attempts fail, third succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "osascript"),
            subprocess.CalledProcessError(1, "osascript"),
            Mock(stdout="75\n", returncode=0),
        ]
        
        volume = controller.get_volume()
        
        assert volume == 75
        assert mock_run.call_count == 3

    @pytest.mark.integration 
    def test_config_validation_integration(self):
        """Test config validation with various scenarios."""
        # Valid config should not raise
        valid_config = Config()
        valid_config.validate()
        
        # Invalid configs should raise
        invalid_configs = [
            Config(target_volume=150),
            Config(active_interval=-1),
            Config(audio_threshold=0),
            Config(call_activity_ratio=1.5),
        ]
        
        for config in invalid_configs:
            with pytest.raises(ValueError):
                config.validate()
