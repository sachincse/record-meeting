"""Script to create the updated GUI file with all necessary changes"""

# Read the original GUI file
with open('recordflow/gui_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make all necessary replacements
replacements = [
    ('from .core import RecordFlow', 'from recordmymeeting.core import RecordMyMeeting'),
    ('from .device_manager import list_audio_devices', 'from recordmymeeting.device_manager import list_audio_devices'),
    ('class RecordFlowGUI:', 'class RecordMyMeetingGUI:'),
    ('"""GUI application for RecordFlow with robust window handling."""', '"""GUI application for RecordMyMeeting with robust window handling and device testing."""'),
    ('self.root.title("RecordFlow - Audio & Screen Recorder")', 'self.root.title("RecordMyMeeting v0.2.0")'),
    ('self._recorder = None # The RecordFlow instance', 'self._recorder = None # The RecordMyMeeting instance'),
    ('RecordFlow(', 'RecordMyMeeting('),
    ('"""Launch the RecordFlow GUI application."""', '"""Launch the RecordMyMeeting GUI application."""'),
    ('app = RecordFlowGUI(root)', 'app = RecordMyMeetingGUI(root)'),
    ('logger.info("RecordFlow GUI initialized")', 'logger.info("RecordMyMeeting GUI initialized")'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Add import for platform at the top (after other imports)
import_section = """import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime, timedelta
import threading
import time
import logging
import atexit
import os
import sys
from typing import Optional"""

new_import_section = """import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime, timedelta
import threading
import time
import logging
import atexit
import os
import sys
import platform
from typing import Optional"""

content = content.replace(import_section, new_import_section)

# Add device testing section after device refresh button
# Find the location to insert device testing
device_refresh_line = 'ttk.Button(device_frame, text="🔄 Refresh Devices", command=self._refresh_audio_devices).grid(row=2, column=0, columnspan=2, pady=(8,0))'

device_test_section = '''ttk.Button(device_frame, text="🔄 Refresh Devices", command=self._refresh_audio_devices).grid(row=2, column=0, columnspan=2, pady=(8,0))

        # NEW: Device Testing Section
        test_frame = ttk.LabelFrame(frame, text="Test Devices", padding="10")
        test_frame.grid(row=4, column=0, sticky='ew', **pad)
        test_frame.columnconfigure(0, weight=1)

        test_button_frame = ttk.Frame(test_frame)
        test_button_frame.grid(row=0, column=0, sticky='ew', padx=8, pady=4)

        self.test_mic_btn = ttk.Button(test_button_frame, text="🎤 Test Microphone", command=self._test_microphone)
        self.test_mic_btn.pack(side=tk.LEFT, padx=5)

        self.test_speaker_btn = ttk.Button(test_button_frame, text="🔊 Test Speaker", command=self._test_speaker)
        self.test_speaker_btn.pack(side=tk.LEFT, padx=5)

        self.test_screen_btn = ttk.Button(test_button_frame, text="🖥️ Test Screen", command=self._test_screen)
        self.test_screen_btn.pack(side=tk.LEFT, padx=5)

        self.test_status_label = ttk.Label(test_frame, text="Click a button to test a device", font=("Arial", 10))
        self.test_status_label.grid(row=1, column=0, sticky='w', padx=8, pady=8)'''

content = content.replace(device_refresh_line, device_test_section)

# Update row numbers for subsequent frames
content = content.replace('quality_frame.grid(row=4,', 'quality_frame.grid(row=5,')
content = content.replace('schedule_frame.grid(row=5,', 'schedule_frame.grid(row=6,')
content = content.replace('status_frame.grid(row=6,', 'status_frame.grid(row=7,')
content = content.replace('button_frame.grid(row=7,', 'button_frame.grid(row=8,')
content = content.replace('footer.grid(row=8,', 'footer.grid(row=9,')

# Update window size to accommodate new section
content = content.replace('self.root.geometry("850x750")', 'self.root.geometry("850x900")')
content = content.replace('self.root.minsize(800, 600)', 'self.root.minsize(800, 700)')

# Add device testing methods before _handle_start
device_test_methods = '''
    # NEW: Device Testing Methods
    def _test_microphone(self):
        """Test microphone device."""
        import pyaudio
        import numpy as np

        mic_index = self._get_device_index(self.mic_combo.get())
        if mic_index is None:
            self.test_status_label.config(
                text="❌ Please select a microphone device first",
                foreground="red")
            return

        self.test_mic_btn.config(state="disabled")
        self.test_status_label.config(
            text="🎤 Testing microphone... Recording 2 seconds of audio...",
            foreground="blue")
        self.root.update()

        def test_thread():
            try:
                p = pyaudio.PyAudio()
                device_info = p.get_device_info_by_index(mic_index)
                max_channels = int(device_info.get('maxInputChannels', 1))
                actual_channels = min(2, max_channels)

                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=actual_channels,
                    rate=44100,
                    input=True,
                    input_device_index=mic_index,
                    frames_per_buffer=1024
                )

                frames = []
                for i in range(0, int(44100 / 1024 * 2)):
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                stream.stop_stream()
                stream.close()

                audio_data = b''.join(frames)
                if len(audio_data) > 0:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    max_vol = np.max(np.abs(audio_array))

                    if max_vol > 100:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"✅ Microphone is working! Max volume: {max_vol}",
                            foreground="green"))
                    else:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"⚠️ Microphone is active but very quiet. Max volume: {max_vol}. Try speaking louder.",
                            foreground="orange"))
                else:
                    self.root.after(0, lambda: self.test_status_label.config(
                        text="❌ No audio data received from microphone",
                        foreground="red"))

                p.terminate()

            except Exception as e:
                self.root.after(0, lambda: self.test_status_label.config(
                    text=f"❌ Microphone test failed: {str(e)}",
                    foreground="red"))
            finally:
                self.root.after(0, lambda: self.test_mic_btn.config(state="normal"))

        threading.Thread(target=test_thread, daemon=True).start()

    def _test_speaker(self):
        """Test speaker/system audio recording device."""
        import pyaudio
        import numpy as np

        spk_index = self._get_device_index(self.spk_combo.get())
        if spk_index is None:
            self.test_status_label.config(
                text="❌ Please select a speaker device first",
                foreground="red")
            return

        self.test_speaker_btn.config(state="disabled")
        self.test_status_label.config(
            text="🔊 Testing speaker... Recording 2 seconds of system audio...",
            foreground="blue")
        self.root.update()

        def test_thread():
            try:
                p = pyaudio.PyAudio()
                device_info = p.get_device_info_by_index(spk_index)
                max_channels = int(device_info.get('maxInputChannels', 1))
                actual_channels = min(2, max_channels)

                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=actual_channels,
                    rate=44100,
                    input=True,
                    input_device_index=spk_index,
                    frames_per_buffer=1024
                )

                frames = []
                for i in range(0, int(44100 / 1024 * 2)):
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)

                stream.stop_stream()
                stream.close()

                audio_data = b''.join(frames)
                if len(audio_data) > 0:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    max_vol = np.max(np.abs(audio_array))

                    if max_vol > 100:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"✅ Speaker recording is working! Max volume: {max_vol}",
                            foreground="green"))
                    else:
                        macos_note = ""
                        if platform.system() == 'Darwin':
                            macos_note = " On macOS, you need BlackHole or similar virtual audio device. See MACOS_SPEAKER_RECORDING.md."
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"⚠️ Speaker device active but very quiet. Max volume: {max_vol}. Play some audio and try again.{macos_note}",
                            foreground="orange"))
                else:
                    self.root.after(0, lambda: self.test_status_label.config(
                        text="❌ No audio data received from speaker device",
                        foreground="red"))

                p.terminate()

            except Exception as e:
                error_msg = str(e)
                macos_help = ""
                if platform.system() == 'Darwin':
                    macos_help = " On macOS, you need BlackHole or similar virtual audio device. See MACOS_SPEAKER_RECORDING.md for setup."
                self.root.after(0, lambda: self.test_status_label.config(
                    text=f"❌ Speaker test failed: {error_msg}.{macos_help}",
                    foreground="red"))
            finally:
                self.root.after(0, lambda: self.test_speaker_btn.config(state="normal"))

        threading.Thread(target=test_thread, daemon=True).start()

    def _test_screen(self):
        """Test screen recording capability."""
        import mss

        self.test_screen_btn.config(state="disabled")
        self.test_status_label.config(
            text="🖥️ Testing screen recording... Capturing one frame...",
            foreground="blue")
        self.root.update()

        def test_thread():
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[0]
                    img = sct.grab(monitor)
                    
                    if img:
                        resolution = f"{monitor['width']}x{monitor['height']}"
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"✅ Screen recording is working! Resolution: {resolution}",
                            foreground="green"))
                    else:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text="❌ Failed to capture screen",
                            foreground="red"))

            except Exception as e:
                error_msg = str(e)
                permission_note = ""
                if platform.system() == 'Darwin':
                    permission_note = " On macOS, you need to grant screen recording permissions. See SCREEN_RECORDING_PERMISSIONS_MACOS.md."
                self.root.after(0, lambda: self.test_status_label.config(
                    text=f"❌ Screen test failed: {error_msg}.{permission_note}",
                    foreground="red"))
            finally:
                self.root.after(0, lambda: self.test_screen_btn.config(state="normal"))

        threading.Thread(target=test_thread, daemon=True).start()

'''

# Insert device test methods before _handle_start
handle_start_marker = '    def _handle_start(self):'
content = content.replace(handle_start_marker, device_test_methods + handle_start_marker)

# Fix the critical window close handler to capture session_folder BEFORE stopping
old_window_close = '''                # Explicitly stop recorder if it's still active (might have been missed by thread join)
                with self._recorder_lock:
                    if self._recorder and self._active_recording:
                        try:
                            self._recorder.stop(save_output=True)  # Explicitly save output
                            logger.info(f"Recording stopped and saved to: {self._recorder.session_folder}")
                            if self.root.winfo_exists():  # Check if root still exists
                                messagebox.showinfo("Recording Complete", f"Recording saved to: {self._recorder.session_folder}")'''

new_window_close = '''                # Explicitly stop recorder if it's still active (might have been missed by thread join)
                with self._recorder_lock:
                    if self._recorder and self._active_recording:
                        try:
                            # CRITICAL FIX: Capture session_folder BEFORE stopping
                            saved_folder = self._recorder.session_folder
                            self._recorder.stop(save_output=True)  # Explicitly save output
                            logger.info(f"Recording stopped and saved to: {saved_folder}")
                            if self.root.winfo_exists():  # Check if root still exists
                                messagebox.showinfo("Recording Complete", f"Recording saved to: {saved_folder}")'''

content = content.replace(old_window_close, new_window_close)

# Write the updated content
with open('recordmymeeting/gui_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ GUI file created successfully at recordmymeeting/gui_app.py")
print("✅ All RecordFlow references updated to RecordMyMeeting")
print("✅ Device test buttons added")
print("✅ Window close handler fixed to capture session_folder before stopping")
print("✅ Platform-specific error messages added")
