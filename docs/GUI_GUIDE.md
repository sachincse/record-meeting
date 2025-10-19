# GUI Guide

Graphical user interface for RecordMyMeeting.

## Installation

```bash
pip install recordmymeeting
```

## Launch

```bash
recordmymeeting-gui
```

## Features

### Session Information
- **Session Name**: Custom name for your recording
- **Output Directory**: Choose where recordings are saved
- Automatic timestamping to prevent overwrites

### Recording Options
- **🎤 Record Microphone**: Capture your voice (compliance-friendly)
- **🔊 Record Speaker**: Capture system audio
- **🖥️ Record Screen**: Capture screen display
- Legal compliance warning displayed

### Device Selection
- **Microphone Dropdown**: Select input device
- **Speaker Dropdown**: Select output/loopback device
- **Refresh Button**: Update device list
- Auto-detection of working devices

### Device Testing
- **Test Microphone**: 2-second test with volume feedback
- **Test Speaker**: 2-second system audio test
- **Test Screen**: Single frame capture test
- Real-time status feedback

### Quality Settings
- **Video FPS**: 5-30 frames per second
- **Audio Rate**: 44100 or 48000 Hz
- **Channels**: Mono (1) or Stereo (2)

### Scheduling
- **Enable Schedule**: Toggle scheduled recording
- **Start Time**: 24-hour format (HH:MM)
- **Duration**: Recording length in minutes
- Countdown display before recording starts

### Controls
- **▶ Start Recording**: Begin recording immediately or schedule
- **■ Stop Recording**: Stop and save recording
- **✕ Cancel Schedule**: Cancel scheduled recording

### Status Display
- Real-time recording status
- Countdown timer
- Session folder path on completion

## Usage Examples

### Example 1: Quick Microphone Recording

1. Launch GUI: `recordmymeeting-gui`
2. Check "Record Microphone" only
3. Click "Start Recording"
4. Click "Stop Recording" when done

### Example 2: Scheduled Interview Recording

1. Launch GUI
2. Enter session name: "Google_Interview_Round1"
3. Check "Record Microphone" only
4. Enable "Schedule"
5. Set start time: 14:30
6. Set duration: 60 minutes
7. Click "Start Recording"
8. GUI will wait until 14:30 and record for 60 minutes

### Example 3: Full Recording with Testing

1. Launch GUI
2. Click "Test Microphone" - verify it works
3. Click "Test Speaker" - verify it works
4. Click "Test Screen" - verify it works
5. Check all recording options
6. Click "Start Recording"

## Tips

- **Device Testing**: Always test devices before important recordings
- **Compliance**: Mic-only recording is safest for interviews
- **Scheduling**: Use for hands-free recording
- **Window Close**: Closing window during recording will save it
- **Refresh Devices**: Click refresh if you plug in new devices
- **Scrollable**: Window scrolls on small screens

## Troubleshooting

### No Microphone Detected
- Click "Refresh Devices"
- Check system audio settings
- Ensure microphone is plugged in and enabled

### Speaker Recording Not Working
- On Windows: Enable "Stereo Mix" in sound settings
- On macOS: Install BlackHole or similar virtual audio device
- Test the device before recording

### Screen Recording Permission Denied
- On macOS: Grant screen recording permission in System Preferences
- On Windows: Run as administrator if needed

## Keyboard Shortcuts

- **Mouse Wheel**: Scroll through options
- **Tab**: Navigate between fields
- **Enter**: Activate focused button


