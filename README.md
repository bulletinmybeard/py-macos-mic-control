# py-macos-mic-control

[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey)](https://www.apple.com/macos/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Test](https://github.com/bulletinmybeard/py-macos-mic-control/actions/workflows/test.yml/badge.svg?branch=development)](https://github.com/bulletinmybeard/py-macos-mic-control/actions/workflows/test.yml)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python utility that automatically maintains consistent microphone input volume during calls and meetings on macOS. It detects active audio sessions and adjusts the microphone level accordingly, ensuring your voice comes through at an optimal volume level at all times.

## Features

- Automatic detection of calls and meetings through audio sampling
- Smart microphone volume management
- Continuous background monitoring
- Detailed activity logging with configurable path
- Low resource usage
- Native macOS integration
- Configurable via command-line arguments

## Prerequisites

- macOS (tested on 10.15+)
- Python 3.12+
- Poetry (Python dependency manager)

## Installation

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone this repository:
```bash
git clone https://github.com/bulletinmybeard/py-macos-mic-control.git
cd py-macos-mic-control
```

3. Install dependencies using Poetry:
```bash
poetry install
```

## Usage

### Basic Usage

Run with default settings:
```bash
poetry run mic-control
```

Run with custom settings:
```bash
poetry run mic-control --target-volume 70 --active-interval 5 --log-path ~/logs/mic.log
```

### Command Line Arguments

| Argument | Description | Default | Valid Range |
|:---------|:------------|:---------|:------------|
| `--target-volume` | Target microphone volume level | 80 | 0-100 |
| `--active-interval` | Seconds between checks during calls | 3 | > 0 |
| `--idle-interval` | Seconds between checks when idle | 15 | > 0 |
| `--call-interval` | Seconds between full call detection checks | 30 | > 0 |
| `--log-path` | Path to the log file | `mic_control.log` | Valid file path |

Get help:
```bash
poetry run mic-control --help
```

### Example Commands

1. Set custom target volume:
```bash
poetry run mic-control --target-volume 70
```

2. Adjust check intervals:
```bash
poetry run mic-control --active-interval 5 --idle-interval 20 --call-interval 45
```

3. Specify custom log location:
```bash
poetry run mic-control --log-path /var/log/mic_control/app.log
```

4. Combine multiple options:
```bash
poetry run mic-control --target-volume 75 --active-interval 4 --log-path ~/logs/mic.log
```

### Running in Background

To run the script in the background:
```bash
poetry run mic-control &
```

## CI/CD

This project uses GitHub Actions for continuous integration and automated testing. The workflow runs on push to `development` branch and pull requests to `master` and `development` branches.

### Workflow Jobs

| Job | Description | Dependencies |
|:---------|:------------|:---------|
| `setup` | Configures Poetry and installs dependencies | None |
| `lint` | Runs code quality checks (isort, black, flake8) | `setup` |
| `test` | Runs pytest with coverage reporting | `setup` |
| `security` | Performs security scans using multiple tools | `setup` |

### Security Scans

The security job runs multiple tools:
- Bandit for Python security linting
- Safety for checking known vulnerabilities
- pip-audit for dependency auditing

### Triggers

- **Push**: Triggered on pushes to `development` branch
- **Pull Request**: Triggered on PRs to `master` and `development` branches
- **Path Filters**: Ignores changes to documentation files and licenses

### Caching

The workflow uses caching for Poetry virtual environments to speed up subsequent runs:
```yaml
key: ${{ runner.os }}-poetry-${{ hashFiles('poetry.lock') }}
```

### Local Testing

You can run the same checks locally:

```bash
# Lint checks
poetry run isort . --check-only --diff
poetry run black . --check --diff
poetry run flake8 .

# Tests with coverage
poetry run pytest tests/ -v --cov=mic_control --cov-report=term-missing

# Security checks
poetry run bandit -r mic_control/ -v
poetry run safety check
poetry run pip-audit
```

### Requirements

The workflow runs on Ubuntu Latest with Python 3.12 and requires these system dependencies:
- `portaudio19-dev`
- `python3-all-dev`

## Security

### Bandit

Bandit is a security linter designed to find common security vulnerabilities in Python code through static analysis.

Run a security check:
```bash
# Basic scan
poetry run bandit -r mic_control/

# Detailed scan with more information
poetry run bandit -r mic_control/ -v

# Most verbose scan with low-level logging and issue info
poetry run bandit -r mic_control/ -ll -ii
```

Command flags:
- `-r`: Recursive scanning
- `-v`: Verbose output showing files scanned and metrics
- `-ll`: Low-level logging (shows configuration details)
- `-ii`: Include more information about issues found

Example output:
```bash
Files in scope (3):
    mic_control/__init__.py (score: {SEVERITY: 0, CONFIDENCE: 0})
    mic_control/__main__.py (score: {SEVERITY: 0, CONFIDENCE: 0})
    mic_control/utils.py (score: {SEVERITY: 0, CONFIDENCE: 0})

Test results:
    No issues identified.

Code scanned:
    Total lines of code: 189
    Total lines skipped (#nosec): 2
```

The project uses Bandit configurations in `pyproject.toml` and inline code comments to manage security exceptions where appropriate.

## Development

### Testing

Run basic tests:
```bash
poetry run pytest
```

Run tests with coverage:
```bash
poetry run pytest --cov=mic_control
```

Run verbose tests:
```bash
poetry run pytest -vv
```

### Code Style

The project adheres to Python code quality standards using:
- Black for code formatting (line length: 100)
- isort for import sorting
- Flake8 for linting

Format code:
```bash
poetry run black .
poetry run isort .
poetry run flake8 .
```

## Logging

The script maintains a detailed log file that includes:
- Call detection status changes
- Volume adjustments
- Error messages
- Timestamp for each event

Example log output:
```bash
2024-10-24 13:15:52,295 - Starting microphone level controller with audio detection
2024-10-24 13:16:03,483 - Call status check: in call
2024-10-24 13:16:07,231 - In call: Adjusting volume from 74 to 80
2024-10-24 13:16:13,948 - In call: Adjusting volume from 61 to 80
2024-10-24 13:16:20,709 - In call: Adjusting volume from 65 to 80
2024-10-24 13:16:35,104 - Call status check: not in call
2024-10-24 13:17:16,222 - Call status check: in call
2024-10-24 13:17:16,449 - In call: Adjusting volume from 38 to 80
2024-10-24 13:17:47,492 - Call status check: in call
2024-10-24 13:17:47,741 - In call: Adjusting volume from 67 to 80
2024-10-24 13:18:18,348 - Call status check: in call
2024-10-24 13:18:18,585 - In call: Adjusting volume from 39 to 80
2024-10-24 13:18:49,137 - Call status check: in call
2024-10-24 13:18:49,368 - In call: Adjusting volume from 65 to 80
2024-10-24 13:18:56,058 - In call: Adjusting volume from 54 to 80
2024-10-24 13:19:02,783 - In call: Adjusting volume from 52 to 80
2024-10-24 13:19:20,354 - Call status check: in call
2024-10-24 13:19:20,590 - In call: Adjusting volume from 42 to 80
2024-10-24 13:19:24,030 - In call: Adjusting volume from 67 to 80
2024-10-24 13:19:51,336 - Call status check: not in call
2024-10-24 13:20:32,464 - Call status check: not in call
2024-10-24 13:21:13,591 - Call status check: not in call
2024-10-24 13:21:54,726 - Call status check: not in call
2024-10-24 13:22:35,877 - Call status check: not in call
2024-10-24 13:23:17,015 - Call status check: not in call
2024-10-24 13:23:58,146 - Call status check: not in call
2024-10-24 13:24:39,274 - Call status check: not in call
2024-10-24 13:25:20,390 - Call status check: not in call
2024-10-24 13:26:01,510 - Call status check: in call
2024-10-24 13:26:01,756 - In call: Adjusting volume from 30 to 80
2024-10-24 13:26:05,225 - In call: Adjusting volume from 61 to 80
2024-10-24 13:26:08,693 - In call: Adjusting volume from 49 to 80
2024-10-24 13:26:18,638 - In call: Adjusting volume from 55 to 80
2024-10-24 13:26:32,981 - Call status check: in call
2024-10-24 13:26:33,217 - In call: Adjusting volume from 26 to 80
2024-10-24 13:26:36,666 - In call: Adjusting volume from 24 to 80
2024-10-24 13:26:40,113 - In call: Adjusting volume from 64 to 80
2024-10-24 13:26:43,556 - In call: Adjusting volume from 65 to 80
2024-10-24 13:26:50,238 - In call: Adjusting volume from 55 to 80
2024-10-24 13:27:04,636 - Call status check: in call
2024-10-24 13:27:04,887 - In call: Adjusting volume from 36 to 80
2024-10-24 13:27:08,326 - In call: Adjusting volume from 64 to 80
```

## Technical Details

### Call Detection

The script determines if you're in a call by:
1. Sampling audio input at regular intervals
2. Calculating RMS (Root Mean Square) value of the audio
3. Comparing against a threshold
4. Requiring sustained audio activity (40% of samples) to confirm call status

### Volume Control

Uses macOS's `osascript` to:
- Read current microphone volume
- Set new volume levels
- Maintain target volume during calls

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

1. If the script can't access your microphone:
    - Check microphone permissions in System Preferences
    - Ensure no other application is exclusively using the microphone

2. If volume adjustments don't work:
    - Verify you have permission to run osascript
    - Check if your microphone supports volume adjustments

3. For logging issues:
    - Ensure write permissions for the log file location
    - Check available disk space
