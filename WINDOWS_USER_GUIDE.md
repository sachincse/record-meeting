# RecordMyMeeting - Windows User Guide

## Quick Start

### Installation
```bash
# Clone or download the repository
cd record-meeting

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Launch GUI
```bash
recordmymeeting-gui
```

## Common Issues and Solutions

### 1. ❌ Window Close Button Not Working
**Status**: ✅ FIXED in v0.2.0

The window close button now properly handles all scenarios:
- **When recording is active**: Shows dialog with 3 options (Save/Don't Save/Cancel)
- **When no recording**: Closes normally
- **When scheduled**: Allows cancellation

### 2. ❌ Speaker Recording Fails - "Invalid number of channels"
**Problem**: Most Windows speaker devices don't support direct recording.

**Solution**: Enable "Stereo Mix" device

#### How to Enable Stereo Mix on Windows 11/10:

1. **Right-click** the speaker icon in the system tray
2. Click **"Sound settings"** or **"Open Sound settings"**
3. Scroll down and click **"More sound settings"** or **"Sound Control Panel"**
4. Go to the **"Recording"** tab
5. **Right-click** in the empty space and check:
   - ✅ **"Show Disabled Devices"**
   - ✅ **"Show Disconnected Devices"**
6. You should now see **"Stereo Mix"**
7. **Right-click** on "Stereo Mix" and select **"Enable"**
8. **Right-click** again and select **"Set as Default Device"** (optional)
9. Click **"OK"**

#### Alternative: Use Virtual Audio Cable
If Stereo Mix is not available:
- Install **VB-Audio Virtual Cable** (free): https://vb-audio.com/Cable/
- Or **VoiceMeeter** (free): https://vb-audio.com/Voicemeeter/

### 3. ⚠️ Microphone Test Shows "Too Quiet"
**Problem**: Microphone volume threshold was too high (100).

**Solution**: ✅ FIXED in v0.2.0 - Threshold lowered to 50

**Additional Tips**:
- Check Windows microphone settings:
  1. Right-click speaker icon → Sound settings
  2. Scroll to "Input" section
  3. Click on your microphone
  4. Adjust "Input volume" slider
  5. Test microphone and ensure the blue bar moves when you speak

- Check application-specific microphone boost:
  1. Sound Control Panel → Recording tab
  2. Double-click your microphone
  3. Go to "Levels" tab
  4. Increase "Microphone" and "Microphone Boost" sliders

### 4. ❌ Only Screen File Created, No Audio Files
**Problem**: Audio recording failed but screen recording succeeded.

**Root Causes**:
1. **Speaker device doesn't support input** (maxInputChannels = 0)
   - Solution: Use Stereo Mix (see #2 above)
   
2. **Microphone device not properly selected**
   - Solution: Click "Refresh Devices" and select correct microphone
   
3. **Permissions issue**
   - Solution: Check Windows Privacy Settings:
     - Settings → Privacy & Security → Microphone
     - Ensure "Microphone access" is ON
     - Ensure "Let apps access your microphone" is ON

**Verification Steps**:
1. Launch `recordmymeeting-gui`
2. Click **"Test Microphone"** button
   - Should show: ✅ "Microphone is working! Max volume: XXX"
3. Click **"Test Speaker"** button
   - Should show: ✅ "Speaker recording is working! Max volume: XXX"
4. Click **"Test Screen"** button
   - Should show: ✅ "Screen recording is working! Resolution: XXXXxXXXX"

### 5. 📁 Finding Your Recordings
Default location: `./recordings/`

Each recording session creates a folder with timestamp:
```
recordings/
  └── recording_20251019_163000/
      ├── screen.mp4          # Screen recording
      ├── microphone.wav      # Your voice
      ├── speaker.wav         # System audio
      └── merged.wav          # Combined mic + speaker
```

## Device Selection Tips

### Microphone Devices
Look for these in the device list:
- **Built-in Microphone** - Laptop mic
- **USB Microphone** - External USB mic
- **Headset Microphone** - Gaming/call headset
- **Array Microphone** - Multi-mic array
- **Bluetooth Microphone** - Wireless headset

### Speaker/System Audio Devices
For recording system audio, look for:
- **Stereo Mix** ⭐ (Best option for Windows)
- **WASAPI Loopback** devices
- **Virtual Audio Cable** devices
- **VoiceMeeter** devices

**Note**: Regular speaker output devices (like "Speakers" or "Headphones") will show "Invalid number of channels" error because they don't support input recording.

## CLI Usage

### List Available Devices
```bash
recordmymeeting --list-devices
```

### Record Microphone Only (Compliance-Friendly)
```bash
recordmymeeting --source mic --duration 30
```

### Record Everything
```bash
recordmymeeting --source all --duration 30
```

### Record with Specific Devices
```bash
# First, list devices to get indices
recordmymeeting --list-devices

# Then record with specific device indices
recordmymeeting --source all --mic-device 1 --speaker-device 44 --duration 30
```

### Schedule Recording
```bash
recordmymeeting --source mic --schedule 14:30 --duration 60
```

## Troubleshooting

### Error: "Failed to open speaker stream: Invalid audio channels"
**Meaning**: The selected speaker device doesn't support input recording.

**Solution**:
1. Enable Stereo Mix (see section #2 above)
2. In the GUI, click "Refresh Devices"
3. Select "Stereo Mix" from the Speaker dropdown
4. Click "Test Speaker" to verify it works

### Error: "No microphone detected"
**Solution**:
1. Check if microphone is plugged in
2. Check Windows Privacy Settings (Settings → Privacy → Microphone)
3. Try a different USB port (for USB mics)
4. Restart the application

### GUI Doesn't Launch
**Solution**:
```bash
# Make sure you're in the virtual environment
venv\Scripts\Activate.ps1

# Reinstall the package
pip install -e .

# Try launching again
recordmymeeting-gui
```

### Recording Stops Immediately
**Possible causes**:
1. No recording source selected (check at least one: Mic/Speaker/Screen)
2. Device initialization failed (check logs)
3. Permissions issue

**Solution**:
- Check the status message in the GUI
- Look at console output for error messages
- Use device test buttons to verify each component works

## Performance Tips

### For Long Recordings
- **Lower FPS**: Use 5-10 FPS instead of 30 for screen recording
- **Close unnecessary apps**: Free up system resources
- **Use SSD**: Save recordings to SSD for better performance
- **Monitor disk space**: Ensure sufficient space (1 hour ≈ 1-2 GB)

### For Better Quality
- **Higher FPS**: Use 20-30 FPS for smooth screen recording
- **48000 Hz audio**: Use 48000 Hz instead of 44100 Hz
- **Stereo**: Use 2 channels instead of 1 for richer audio
- **External mic**: Use USB microphone for better voice quality

## Legal Compliance

### Recording Your Own Voice (Microphone Only)
- ✅ Generally legal in most jurisdictions
- ✅ No consent needed (you're recording yourself)
- ✅ Recommended for interviews, meetings, lectures

### Recording System Audio / Others' Voices
- ⚠️ May require consent depending on jurisdiction
- ⚠️ Check local laws (one-party vs two-party consent)
- ⚠️ Inform participants before recording
- ⚠️ Some platforms (Zoom, Teams) have built-in recording with notifications

**Best Practice**: Always inform participants and get consent before recording.

## Support

### Check Logs
The application logs important information. Look for:
- Device detection messages
- Stream opening success/failure
- Recording start/stop events
- Error messages with details

### Report Issues
When reporting issues, include:
1. Windows version
2. Python version (`python --version`)
3. Full error message from console
4. Output of `recordmymeeting --list-devices`
5. Steps to reproduce the issue

## Version History

### v0.2.0 (Current)
- ✅ Fixed window close button not working
- ✅ Fixed speaker file not being created (Bug #1)
- ✅ Fixed merged file creation error (Bug #2)
- ✅ Lowered microphone test threshold (100 → 50)
- ✅ Added device test buttons in GUI
- ✅ Added better error messages for invalid channels
- ✅ Implemented dynamic device switching
- ✅ Improved Windows compatibility

### v0.1.2 (Previous)
- Initial release as RecordFlow
- Basic recording functionality
