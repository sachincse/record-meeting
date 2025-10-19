# Changelog

All notable changes to RecordMyMeeting will be documented in this file.

## [0.2.0] - 2025-10-19

### Added
- PyPI package structure and metadata
- Automated GitHub Actions release workflow
- Comprehensive documentation (README, RELEASING, CONTRIBUTING)
- Python API examples
- Hardware-independent test suite

### Changed
- Package renamed from `recordflow` to `recordmymeeting`
- CLI command: `recordflow` → `recordmymeeting`
- GUI command: `recordflow-gui` → `recordmymeeting-gui`
- Updated all imports and module references
- Improved setup.py with dynamic versioning

### Fixed
- Test suite now works without audio hardware
- Proper package metadata for PyPI

## [0.1.2] - Previous
- Fixed CLI --mic flag to record mic-only
- Added device classification and scoring
- Improved --list-devices output
- Robust GUI with scrollable canvas and compliance warning

## [0.1.1] - Previous
- Added scheduled recording
- Improved device auto-detection
- CLI improvements

## [0.1.0] - Initial
- Initial release
- Basic recording functionality
