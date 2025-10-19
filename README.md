
# RecordMyMeeting

[![PyPI version](https://badge.fury.io/py/recordmymeeting.svg)](https://badge.fury.io/py/recordmymeeting)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Effortlessly capture audio and screen with intelligent device detection. Perfect for recording interviews, meetings, demos, and tutorials.

## Features

- 🎤 **Microphone Recording** - Capture your voice with auto-device detection
- 🔊 **System Audio Recording** - Record speaker/system output (Windows/macOS)
- 🖥️ **Screen Recording** - Capture your display at configurable FPS
- ⏰ **Scheduled Recording** - Set recordings to start at specific times
- 🎨 **GUI & CLI** - Choose between graphical or command-line interface
- 🔍 **Smart Device Detection** - Automatically finds best audio devices
- ✅ **Compliance-Friendly** - Defaults to mic-only for legal safety

## Installation

```bash
pip install recordmymeeting
```

## Quick Start

### Command Line

```bash
# List available devices
recordmymeeting --list-devices

# Record your microphone
recordmymeeting --source mic --duration 5

# Get help
recordmymeeting -h
```

### Graphical Interface

```bash
recordmymeeting-gui
```

## CLI Usage

```bash
# List devices
recordmymeeting --list-devices

# Record only your microphone (compliance-friendly)
recordmymeeting --source mic --duration 5 --session-name "Test"

# Schedule a 10-minute recording at 14:30
recordmymeeting --source mic --schedule 14:30 --duration 10
```

## Python API

```python
from recordmymeeting.core import RecordMyMeeting

# Record your microphone for ~10 seconds
rec = RecordMyMeeting(
    record_mic=True,
    record_speaker=False,
    record_screen=False,
    session_name="quick_demo",
)
rec.start()
import time; time.sleep(10)
rec.stop()
```

## GUI Usage

Launch with:

```bash
recordmymeeting-gui
```

## Documentation

- **[CLI Guide](docs/CLI_GUIDE.md)** - Complete command-line reference
- **[GUI Guide](docs/GUI_GUIDE.md)** - Graphical interface tutorial
- **[API Reference](docs/API.md)** - Python API documentation
- **[Contributing](CONTRIBUTING.md)** - Development guidelines
- **[Changelog](CHANGELOG.md)** - Version history
- **[Legal Compliance](LEGAL_COMPLIANCE.md)** - Recording laws and best practices

## Releasing

- **[Manual Release Guide](RELEASING.md)** - Step-by-step PyPI publishing
- **[GitHub Actions Setup](GITHUB_ACTIONS_SETUP.md)** - Automated release workflow

## Legal Compliance

⚠️ **Important**: Recording laws vary by jurisdiction. Always obtain consent before recording audio or screen. See [LEGAL_COMPLIANCE.md](LEGAL_COMPLIANCE.md) for details.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For issues and questions:
- 🐛 [Report bugs](https://github.com/sachincse/recordmymeeting/issues)
- 💡 [Request features](https://github.com/sachincse/recordmymeeting/issues)
- 📖 [Read documentation](docs/)

