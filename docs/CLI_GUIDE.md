# CLI Guide

Complete command-line interface reference for RecordMyMeeting.

## Installation

```bash
pip install recordmymeeting
```

## Basic Usage

### List Available Devices

```bash
recordmymeeting --list-devices
```

Shows all available audio devices with their indices and classifications.

### Record Microphone Only (Compliance-Friendly)

```bash
recordmymeeting --source mic --duration 5 --session-name "Interview"
```

Records only your microphone for 5 minutes.

### Record Everything

```bash
recordmymeeting --source all --duration 10 --output ./recordings
```

Records microphone, speaker, and screen for 10 minutes.

### Schedule a Recording

```bash
recordmymeeting --source mic --schedule 14:30 --duration 60
```

Schedules a 60-minute recording to start at 2:30 PM.

## Command Reference

### Source Selection

```bash
--source {mic,speaker,screen,all}
```

Specify what to record:
- `mic` - Only your microphone (compliance-friendly)
- `speaker` - System audio/speaker output
- `screen` - Screen capture
- `all` - Microphone + speaker + screen

**Default:** `mic` (if no source specified)

### Recording Options

```bash
-d, --duration MINUTES        # Recording duration in minutes
--session-name NAME           # Custom name for recording folder
-o, --output PATH             # Output directory (default: ./recordings)
--schedule HH:MM              # Schedule start time (24-hour format)
```

### Device Selection

```bash
--mic-device INDEX            # Specific microphone device index
--speaker-device INDEX        # Specific speaker device index
```

Use `--list-devices` to see available device indices.

### Advanced Options

```bash
--fps FPS                     # Video frames per second (default: 10)
--audio-rate RATE             # Audio sample rate in Hz (default: 44100)
-v, --verbose                 # Enable verbose logging
```

### Information

```bash
--list-devices                # List all audio devices
--version                     # Show version
--help                        # Show help message
```

## Examples

### Example 1: Quick Mic Recording

```bash
recordmymeeting --source mic --duration 5
```

### Example 2: Interview Recording with Custom Name

```bash
recordmymeeting --source mic --session-name "Google_Interview_Round2" --duration 60
```

### Example 3: Screen Demo with Audio

```bash
recordmymeeting --source all --duration 15 --session-name "Product_Demo"
```

### Example 4: Scheduled Meeting Recording

```bash
recordmymeeting --source mic --schedule 09:00 --duration 30 --session-name "Daily_Standup"
```

### Example 5: Specific Device Selection

```bash
# First, list devices
recordmymeeting --list-devices

# Then use specific device
recordmymeeting --source mic --mic-device 2 --duration 10
```

### Example 6: High-Quality Recording

```bash
recordmymeeting --source all --fps 30 --audio-rate 48000 --duration 20
```

## Output Structure

Recordings are saved in timestamped folders:

```
recordings/
└── SessionName_20251019_143025/
    ├── microphone.wav
    ├── speaker.wav
    ├── merged.wav
    └── screen.mp4
```

## Tips

- Use `--source mic` for compliance-friendly interview recordings
- Always check `--list-devices` if auto-detection fails
- Use `--schedule` for hands-free recording
- Press `Ctrl+C` to stop recording early
- Recordings are saved even if interrupted


