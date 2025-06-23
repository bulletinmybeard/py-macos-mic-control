# Test Suite

This directory contains the test suite for py-macos-mic-control, organized into unit and integration tests.

## Structure

```
tests/
├── unit/               # Isolated unit tests with mocked dependencies
│   ├── test_audio_monitor.py
│   ├── test_config.py
│   ├── test_utils.py
│   └── test_volume_controller.py
├── integration/        # Integration tests for component interactions
│   └── test_main.py
└── conftest.py        # Shared pytest fixtures
```

## Running Tests

### Run all tests:
```bash
poetry run pytest
```

### Run only unit tests:
```bash
poetry run pytest tests/unit/
```

### Run only integration tests:
```bash
poetry run pytest tests/integration/
```

### Run with coverage:
```bash
poetry run pytest --cov=mic_control --cov-report=term-missing
```

### Run tests by marker:
```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests  
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"
```

### Run specific test file:
```bash
poetry run pytest tests/unit/test_audio_monitor.py
```

### Run specific test:
```bash
poetry run pytest tests/unit/test_audio_monitor.py::TestAudioMonitor::test_is_audio_active_true
```

## Test Categories

### Unit Tests
- **test_audio_monitor.py**: Tests for AudioMonitor class with mocked sounddevice
- **test_volume_controller.py**: Tests for VolumeController implementations with mocked subprocess
- **test_config.py**: Tests for Config class with mocked file operations
- **test_utils.py**: Tests for utility functions with mocked file system

### Integration Tests
- **test_main.py**: Tests for the main application flow, command-line parsing, and component integration

## Writing Tests

When adding new tests:
1. Unit tests should mock all external dependencies
2. Integration tests should test real component interactions
3. Use the shared fixtures from `conftest.py` when possible
4. Add appropriate markers (@pytest.mark.unit, @pytest.mark.integration)
5. Follow the existing naming conventions