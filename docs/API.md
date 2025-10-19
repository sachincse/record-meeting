
# API Reference

## Core Module

### class RecordMyMeeting

Main class for recording audio and screen.

```python
from recordmymeeting.core import RecordMyMeeting
```

#### `__init__(...)`

Create a new recording session.

**Parameters:**
- `output_dir` (str): Output directory for recordings (default: "./recordings")
- `mic_index` (int, optional): Microphone device index (auto-detect if None)
- `speaker_index` (int, optional): Speaker device index (auto-detect if None)
- `record_mic` (bool): Record microphone audio (default: True)
- `record_speaker` (bool): Record speaker/system audio (default: True)
- `record_screen` (bool): Record screen (default: True)
- `video_fps` (int): Video frames per second (default: 10)
- `audio_rate` (int): Audio sample rate in Hz (default: 44100)
- `channels` (int): Number of audio channels (default: 1)
- `session_name` (str, optional): Name for session folder

**Example:**
```python
rec = RecordMyMeeting(
    record_mic=True,
    record_speaker=False,
    record_screen=False,
    session_name="my_recording"
)
```

#### `start()`

Start recording (mic, speaker, screen as configured).

**Returns:** None

**Example:**
```python
rec.start()
```

#### `stop(save_output=True)`

Stop recording and save files.

**Parameters:**
- `save_output` (bool): If False, discard recording data (default: True)

**Returns:** None

**Example:**
```python
rec.stop()
```

#### `get_status()`

Get current recording status.

**Returns:** dict with keys:
- `recording` (bool): Whether currently recording
- `session_folder` (str): Path to session folder
- `record_mic` (bool): Microphone recording enabled
- `record_speaker` (bool): Speaker recording enabled
- `record_screen` (bool): Screen recording enabled
- `mic_file` (str): Path to microphone audio file
- `speaker_file` (str): Path to speaker audio file
- `video_file` (str): Path to video file
- `merged_file` (str): Path to merged audio file

## Device Manager Module

```python
from recordmymeeting.device_manager import (
    list_audio_devices,
    auto_detect_devices,
    classify_device,
    print_all_devices
)
```

### `list_audio_devices()`

List all available audio devices.

**Returns:** dict with keys:
- `microphones` (list): List of microphone devices
- `speakers` (list): List of speaker devices
- `all_devices` (list): All devices combined

**Example:**
```python
devices = list_audio_devices()
for mic in devices['microphones']:
    print(f"[{mic['index']}] {mic['name']}")
```

### `auto_detect_devices()`

Automatically detect working audio devices with smart prioritization.

**Returns:** dict with keys:
- `mic` (dict): Best microphone device info (index, name, channels)
- `speaker` (dict): Best speaker device info (index, name, channels)

**Example:**
```python
devices = auto_detect_devices()
if devices.get('mic'):
    print(f"Using mic: {devices['mic']['name']}")
```

### `classify_device(device_name)`

Classify device type based on name patterns.

**Parameters:**
- `device_name` (str): Name of the audio device

**Returns:** dict with boolean flags:
- `is_headphone`, `is_builtin`, `is_external`, `is_virtual`, `is_mic`, `is_speaker`

### `print_all_devices()`

Print all available devices in a formatted way with classifications.

**Returns:** None (prints to stdout)

**Example:**
```python
print_all_devices()
```

