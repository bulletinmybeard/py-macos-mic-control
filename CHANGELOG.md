# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- No unreleased changes yet

## [0.1.0] - 2024-10-26

### Added
- Core microphone control functionality:
    - Automatic call detection through audio sampling
    - Smart microphone volume management
    - Continuous background monitoring
    - Configurable target volume levels (0-100)
    - Adjustable check intervals for active/idle states
    - Low resource usage implementation
- Command-line interface with configurable arguments:
    - `--target-volume`
    - `--active-interval`
    - `--idle-interval`
    - `--call-interval`
    - `--log-path`
- Comprehensive logging system:
    - Call detection status changes
    - Volume adjustments
    - Error messages
    - Timestamped events
    - Configurable log file location
- CI/CD Pipeline:
    - GitHub Actions workflow setup
    - Automated testing with pytest
    - Code quality checks (black, isort, flake8)
    - Security scanning (bandit, safety, pip-audit)
- Development tooling:
    - Poetry for dependency management
    - pytest configuration for testing
    - Code formatting with Black
    - Import sorting with isort
    - Linting with Flake8
- Documentation:
    - Comprehensive README
    - Installation instructions
    - Usage examples
    - Command-line argument details
    - Troubleshooting guide
    - Technical implementation details

### Security
- Added security scanning with multiple tools:
    - Bandit for Python security linting
    - Safety for known vulnerability checks
    - pip-audit for dependency auditing

[unreleased]: https://github.com/bulletinmybeard/py-macos-mic-control/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bulletinmybeard/py-macos-mic-control/releases/tag/v0.1.0
