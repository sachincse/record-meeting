

# CLI Guide

## Commands

```bash
recordflow --mic --duration 5 --session-name "Test"
recordflow --speaker --screen --duration 10 --output ./my_recordings
recordflow --list-devices
recordflow --schedule 14:30 --duration 10 --mic --session-name "Interview"
recordflow --help
```

## Flags

- `--mic` Record microphone
- `--speaker` Record speaker/system audio
- `--screen` Record screen
- `--duration` Duration in minutes
- `--session-name` Name for session folder
- `--output` Output directory
- `--schedule` Schedule recording at HH:MM (24h)
- `--list-devices` List available audio devices
- `--version` Show version


