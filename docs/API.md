
# API Reference

## RecordFlow

### class RecordFlow

#### __init__(...)
Create a new recording session.

**Parameters:**
- output_dir: Output directory for recordings
- mic_index: Microphone device index
- speaker_index: Speaker device index
- record_mic: Record microphone audio (bool)
- record_speaker: Record speaker/system audio (bool)
- record_screen: Record screen (bool)
- video_fps: Video frames per second
- audio_rate: Audio sample rate
- session_name: Name for session folder

#### start()
Start recording (mic, speaker, screen as configured).

#### stop()
Stop recording and save files.

## Device Manager

### list_input_devices()
Returns a list of available audio input devices with type and score.

### auto_detect_devices()
Returns best microphone and speaker indices based on scoring.

