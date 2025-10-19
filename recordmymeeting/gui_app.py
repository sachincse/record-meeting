import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime, timedelta
import threading
import time
import logging
import atexit
import os
import sys
import platform
from typing import Optional

# Assuming these exist in your project structure
from recordmymeeting.core import RecordMyMeeting
from recordmymeeting.device_manager import list_audio_devices

logger = logging.getLogger(__name__)

class RecordMyMeetingGUI:
    """GUI application for RecordMyMeeting with robust window handling and device testing."""

    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("RecordMyMeeting v0.2.0")
        
        # Thread-safe variables
        self._recorder = None # The RecordMyMeeting instance
        self._recorder_lock = threading.Lock()
        self._stop_flag = threading.Event()
        self._active_recording = False
        self._scheduled = False
        self._recording_thread = None
        self._is_closing = False # Flag to indicate if the GUI is in the process of closing
        self.channels_var = tk.StringVar(value="1") # Default to 1

        # Configure window
        self.root.geometry("850x900")
        self.root.resizable(True, True)
        self.root.minsize(800, 700)

        #Handle window close event
        root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Register cleanup on exit
        # atexit.register(self._cleanup_on_exit) # Removed atexit as it conflicts with _on_window_close
        # _on_window_close handles cleanup now.

        # Store references to images for icons to prevent garbage collection
        self.play_icon = None
        self.stop_icon = None
        self.cancel_icon = None

        # Create scrollable GUI
        self._make_scrollable_gui()
        self._refresh_audio_devices()
        
        logger.info("RecordMyMeeting GUI initialized")

    def _make_scrollable_gui(self):
        """Create a scrollable GUI layout."""
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)

        self.scrollable_frame = ttk.Frame(canvas, padding="10")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            if sys.platform.startswith('win') or sys.platform == 'darwin':
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif sys.platform.startswith('linux'):
                if event.num == 4: # Scroll up
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5: # Scroll down
                    canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel) # Windows/macOS
        canvas.bind_all("<Button-4>", _on_mousewheel) # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel) # Linux scroll down

        self._build_gui_content()


    def _build_gui_content(self):
        """Build the actual GUI content inside the scrollable frame."""
        frame = self.scrollable_frame 
        frame.columnconfigure(0, weight=1)
        
        pad = {'padx': 10, 'pady': 8}

        # Load icons - Make sure you have these files in an 'icons' directory relative to your script
        # Example: if your script is in 'my_app/', put 'play.png' in 'my_app/icons/play.png'
        try:
            icon_dir = os.path.join(os.path.dirname(__file__), "icons") # Assuming 'icons' is next to 'gui_app.py'
            self.play_icon = tk.PhotoImage(file=os.path.join(icon_dir, "play.png")).subsample(2,2) # Adjust subsample as needed
            self.stop_icon = tk.PhotoImage(file=os.path.join(icon_dir, "stop.png")).subsample(2,2)
            self.cancel_icon = tk.PhotoImage(file=os.path.join(icon_dir, "cancel.png")).subsample(2,2)
            icon_available = True
        except tk.TclError:
            logger.warning("Could not load icon images. Buttons will display text only.")
            icon_available = False

        # Title
        title = ttk.Label(frame, text="RecordFlow", font=("Arial", 22, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='ew')

        # Session Information
        session_frame = ttk.LabelFrame(frame, text="Session Information", padding="10")
        session_frame.grid(row=1, column=0, sticky='ew', **pad)
        session_frame.columnconfigure(1, weight=1)

        ttk.Label(session_frame, text="Session Name:").grid(row=0, column=0, sticky='e', padx=8, pady=4)
        self.session_var = tk.StringVar(value=f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        ttk.Entry(session_frame, textvariable=self.session_var, width=40).grid(row=0, column=1, sticky='ew', padx=8, pady=4)

        ttk.Label(session_frame, text="Output Directory:").grid(row=1, column=0, sticky='e', padx=8, pady=4)
        output_frame = ttk.Frame(session_frame)
        output_frame.grid(row=1, column=1, sticky='ew', padx=8, pady=4)
        output_frame.columnconfigure(0, weight=1)

        self.output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "recordings"))
        ttk.Entry(output_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky='ew')    
        ttk.Button(output_frame, text="Browse", command=self._browse_output).grid(row=0, column=1, padx=(4,0))

        # Timestamp note
        note_label = ttk.Label(session_frame, text="Note: Each recording is saved with timestamp to prevent overwriting", font=("Arial", 9), foreground="gray")
        note_label.grid(row=2, column=0, columnspan=2, sticky='ew', padx=8, pady=(0,4))

        # Recording Options
        options_frame = ttk.LabelFrame(frame, text="Recording Options", padding="10")
        options_frame.grid(row=2, column=0, sticky='ew', **pad)

        self.record_mic_var = tk.BooleanVar(value=True)
        self.record_speaker_var = tk.BooleanVar(value=False)
        self.record_screen_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(options_frame, text="🎤 Record Microphone (Your Voice)", 
                        variable=self.record_mic_var).grid(row=0, column=0, sticky='w', padx=8, pady=4)
        
        ttk.Checkbutton(options_frame, text="🔊 Record Speaker/System Audio",
                        variable=self.record_speaker_var).grid(row=0, column=1, sticky='w', padx=8, pady=4)
        ttk.Checkbutton(options_frame, text="🖥️ Record Screen",
                        variable=self.record_screen_var).grid(row=1, column=0, columnspan=2, sticky='w', padx=8, pady=4)
        
        # Compliance warning
        compliance_label = ttk.Label(options_frame, text="⚠ Legal Notice: Recording speaker/screen requires consent. Mic recording (your voice) may also have legal implications depending on your jurisdiction. Ensure you have proper consent for all recordings.",
                                        font=("Arial", 9, "italic"), foreground="orange", wraplength=700)
        compliance_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=8, pady=(8,4))

        # Device Selection
        device_frame = ttk.LabelFrame(frame, text="Device Selection", padding="10")
        device_frame.grid(row=3, column=0, sticky='ew', **pad)
        device_frame.columnconfigure(1, weight=1)

        ttk.Label(device_frame, text="Mic (Input):").grid(row=0, column=0, sticky='e', padx=8, pady=4)
        self.mic_combo = ttk.Combobox(device_frame, state='readonly', width=50)
        self.mic_combo.grid(row=0, column=1, sticky='ew', padx=8, pady=4)

        ttk.Label(device_frame, text="Speaker (Output):").grid(row=1, column=0, sticky='e', padx=8, pady=4) 
        self.spk_combo = ttk.Combobox(device_frame, state='readonly', width=50)
        self.spk_combo.grid(row=1, column=1, sticky='ew', padx=8, pady=4)

        ttk.Button(device_frame, text="🔄 Refresh Devices", command=self._refresh_audio_devices).grid(row=2, column=0, columnspan=2, pady=(8,0))

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
        self.test_status_label.grid(row=1, column=0, sticky='w', padx=8, pady=8)

        # Quality Settings
        quality_frame = ttk.LabelFrame(frame, text="Quality Settings (Optional)", padding="10")
        quality_frame.grid(row=5, column=0, sticky='ew', **pad)

        qual_inner = ttk.Frame(quality_frame)
        qual_inner.pack(fill='x', padx=8, pady=4)

        ttk.Label(qual_inner, text="Video FPS:").pack(side=tk.LEFT, padx=(0, 8))
        self.fps_var = tk.StringVar(value="10")
        ttk.Spinbox(qual_inner, from_=5, to=30, textvariable=self.fps_var, width=8).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(qual_inner, text="Audio Rate (Hz):").pack(side=tk.LEFT, padx=(0, 8))
        self.rate_var = tk.StringVar(value="44100")
        ttk.Combobox(qual_inner, values=("44100", "48000"), textvariable=self.rate_var, width=10, state='readonly').pack(side=tk.LEFT)

        ttk.Label(qual_inner, text="Channels:").pack(side=tk.LEFT, padx=(20, 8))
        ttk.Combobox(qual_inner, values=("1", "2"), textvariable=self.channels_var, width=5, state='readonly').pack(side=tk.LEFT)

        # Scheduling
        schedule_frame = ttk.LabelFrame(frame, text="Schedule (Optional)", padding="10")
        schedule_frame.grid(row=6, column=0, sticky='ew', **pad)

        self.schedule_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(schedule_frame, text="Enable recording schedule", variable=self.schedule_var,
                        command=self._toggle_schedule).grid(row=0, column=0, sticky='w', padx=8, pady=4)
        
        time_frame = ttk.Frame(schedule_frame)
        time_frame.grid(row=1, column=0, sticky='w', padx=8, pady=4)

        ttk.Label(time_frame, text="Start Time (24h):").pack(side=tk.LEFT, padx=(0, 8))
        self.hour_var = tk.StringVar(value=str(datetime.now().hour))
        self.min_var = tk.StringVar(value=str((datetime.now().minute + 5) % 60)) # Default to 5 mins from now

        self.hour_entry = ttk.Entry(time_frame, width=5, textvariable=self.hour_var, state="disabled")
        self.hour_entry.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.min_entry = ttk.Entry(time_frame, width=5, textvariable=self.min_var, state="disabled")
        self.min_entry.pack(side=tk.LEFT)
        ttk.Label(time_frame, text="(hh:mm)").pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(time_frame, text="Duration (minutes):").pack(side=tk.LEFT, padx=(20, 8))
        self.duration_var = tk.StringVar(value="60")
        self.duration_entry = ttk.Entry(time_frame, width=8, textvariable=self.duration_var, state="disabled")
        self.duration_entry.pack(side=tk.LEFT)

        # Status Display
        status_frame = ttk.LabelFrame(frame, text="Status", padding="10")
        status_frame.grid(row=7, column=0, sticky='ew', **pad)

        self.status_label = ttk.Label(status_frame, text="Ready to record", font=("Arial", 11), foreground="green")
        self.status_label.pack(anchor='w', pady=8, padx=4)

        # Control Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=8, column=0, pady=(20, 10))

        if icon_available:
            self.start_btn = ttk.Button(button_frame, text="Start Recording", image=self.play_icon, compound=tk.LEFT, command=self._handle_start, width=20)
            self.stop_btn = ttk.Button(button_frame, text="Stop Recording", image=self.stop_icon, compound=tk.LEFT, command=self._user_stop_recording, width=20, state="disabled")
            self.cancel_btn = ttk.Button(button_frame, text="Cancel Schedule", image=self.cancel_icon, compound=tk.LEFT, command=self._handle_cancel, width=20, state="disabled")
        else: # Fallback to text only if icons are not available
            self.start_btn = ttk.Button(button_frame, text="▶ Start Recording", command=self._handle_start, width=20)
            self.stop_btn = ttk.Button(button_frame, text="■ Stop Recording", command=self._user_stop_recording, width=20, state="disabled")
            self.cancel_btn = ttk.Button(button_frame, text="✕ Cancel Schedule", command=self._handle_cancel, width=20, state="disabled")

        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Footer with tips
        footer = ttk.Label(frame, text="Tip: Ensure you have the necessary permissions before recording audio or screen.",
                            font=("Arial", 9), foreground="gray")
        
        footer.grid(row=9, column=0, sticky='ew', pady=(20,10))


    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)

    def _toggle_schedule(self):
        """Toggle schedule input fields based on checkbox state."""
        state = "normal" if self.schedule_var.get() else "disabled"
        self.hour_entry.config(state=state)
        self.min_entry.config(state=state)
        self.duration_entry.config(state=state)
        self.root.after(0, lambda: self._update_button_states(idle=True)) # Reset buttons when toggling schedule


    def _refresh_audio_devices(self):
        """Refresh the list of available audio devices."""
        try:
            devices = list_audio_devices()

            mic_options = [f"[{dev['index']}] {dev['name']}" for dev in devices['microphones']]
            spk_options = [f"[{dev['index']}] {dev['name']}" for dev in devices['speakers']]

            self.mic_combo['values'] = mic_options
            self.spk_combo['values'] = spk_options

            if mic_options:
                current_mic_val = self.mic_combo.get()
                if current_mic_val in mic_options:
                    self.mic_combo.set(current_mic_val)
                else:
                    self.mic_combo.current(0)
            else:
                self.mic_combo.set("")

            if spk_options:
                current_spk_val = self.spk_combo.get()
                if current_spk_val in spk_options:
                    self.spk_combo.set(current_spk_val)
                else:
                    self.spk_combo.current(min(len(spk_options) - 1, 0))
            else:
                self.spk_combo.set("")

            logger.info("Audio devices refreshed")
        except Exception as e:
            self.root.after(0, lambda: self._safe_messagebox("error", "Error", f"Failed to refresh devices: {e}"))
            logger.error(f"Device refresh error: {e}", exc_info=True)


    def _get_device_index(self, combo_value: str) -> int:
        """Extract device index from combo box value."""
        if not combo_value:
            return None
        try:
            return int(combo_value.split(']')[0][1:])
        except:
            return None



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

                    if max_vol > 50:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"✅ Microphone is working! Max volume: {max_vol}",
                            foreground="green"))
                    else:
                        self.root.after(0, lambda: self.test_status_label.config(
                            text=f"⚠️ Microphone is active but very quiet. Max volume: {max_vol}. Try speaking louder or check microphone settings.",
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

                    if max_vol > 50:
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

    def _handle_start(self):
        """Handle start recording button click."""
        try:
            # Validate inputs
            if not any([self.record_mic_var.get(), self.record_speaker_var.get(), self.record_screen_var.get()]):
                self.root.after(0, lambda: self._safe_messagebox("warning", "No Recording Source", "Please select at least one recording source (microphone, speaker, or screen)."))
                return

            # Get device indices
            mic_index = self._get_device_index(self.mic_combo.get()) if self.record_mic_var.get() else None
            spk_index = self._get_device_index(self.spk_combo.get()) if self.record_speaker_var.get() else None

            # Quality settings
            try:
                fps = int(self.fps_var.get())
                rate = int(self.rate_var.get())
                channels = int(self.channels_var.get())  # Get channels value
            except ValueError:
                fps, rate, channels = 10, 44100, 1  # Default values

            # If scheduled, validate and schedule
            if self.schedule_var.get():
                try:
                    hour = int(self.hour_var.get())
                    minute = int(self.min_var.get())
                    duration = int(self.duration_var.get())

                    if not (0 <= hour <= 23 and 0 <= minute <= 59 and duration > 0):
                        raise ValueError("Invalid time or duration")

                    target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time < datetime.now():  # If target time is in the past, schedule for tomorrow
                        target_time += timedelta(days=1)
                    
                    self._scheduled = True
                    self.root.after(0, lambda: self._update_status(f"Scheduled for {target_time.strftime('%Y-%m-%d %H:%M:%S')}", info=True))
                    self.root.after(0, lambda: self._update_button_states(idle=False, scheduled=True))
                    self._stop_flag.clear()  # Clear stop flag for new schedule

                    self._recording_thread = threading.Thread(
                        target=self._wait_and_record,
                        args=(target_time, duration, mic_index, spk_index, fps, rate, channels),
                        daemon=True
                    )

                    self._recording_thread.start()
                    logger.info(f"Recording scheduled for {target_time} for {duration} minutes.")

                except ValueError:
                    self.root.after(0, lambda: self._safe_messagebox("error", "Invalid Input", "Please enter valid time (hh:mm) and positive duration."))
                    return
            else:
                # Start immediately with channels parameter
                self._start_recording(mic_index, spk_index, fps, rate, channels)

        except Exception as exc:  # Change 'e' to 'exc' to avoid lambda scope issue
            error_msg = str(exc)  # Capture error message
            self.root.after(0, lambda: self._safe_messagebox("error", "Error", f"Failed to start recording: {error_msg}"))
            logger.error(f"Start recording error: {exc}", exc_info=True)


    def _wait_and_record(self, target_time: datetime, duration_minutes: int, mic_index: Optional[int], spk_index: Optional[int], fps: int, rate: int, channels: int):
        """Wait until scheduled time and then start recording."""
        try:
            while datetime.now() < target_time:
                if self._stop_flag.is_set() or self._is_closing:
                    logger.info("Scheduled recording cancelled before start.")
                    self.root.after(0, lambda: self._update_status("Scheduled recording cancelled.", info=True))
                    self.root.after(0, lambda: self._update_button_states(idle=True))
                    self._scheduled = False
                    return
                
                remain = target_time - datetime.now()
                self.root.after(0, lambda: self._update_status(f"Scheduled recording in {str(remain).split('.')[0]}", info=True))
                time.sleep(1)

            # Start recording with channels parameter
            self._start_recording(mic_index, spk_index, fps, rate, channels)   

            # Record for specified duration
            for i in range(duration_minutes * 60):
                if self._stop_flag.is_set() or self._is_closing:
                    logger.info("Scheduled recording stopped manually.")
                    break
                elapsed_min = i // 60
                elapsed_sec = i % 60
                remaining_min = (duration_minutes * 60 - i) // 60
                remaining_sec = (duration_minutes * 60 - i) % 60
                status_text = (f"Recording: {elapsed_min:02d}:{elapsed_sec:02d} (Remaining: {remaining_min:02d}:{remaining_sec:02d}) "
                               f"/ Duration: {duration_minutes}m")
                self.root.after(0, lambda s=status_text: self._update_status(s, recording=True))
                time.sleep(1)

            # Stop recording after duration
            if not self._stop_flag.is_set():
                self._stop_recording()

        except Exception as e:
            logger.error(f"Scheduled recording error: {e}", exc_info=True)
            self.root.after(0, lambda: self._update_status("Error during scheduled recording.", error=True))
            self.root.after(0, lambda: self._update_button_states(idle=True))


    def _start_recording(self, mic_index: Optional[int], spk_index: Optional[int], fps: int, rate: int, channels: int, scheduled_duration: Optional[int] = None):
        """Start the actual recording."""
        try:
            with self._recorder_lock:
                self._recorder = RecordMyMeeting(
                    record_mic=self.record_mic_var.get(),
                    record_speaker=self.record_speaker_var.get(),
                    record_screen=self.record_screen_var.get(),
                    mic_index=mic_index,
                    speaker_index=spk_index,
                    video_fps=fps,
                    audio_rate=rate,
                    channels=channels,  # Add channels parameter
                    output_dir=self.output_dir.get(),
                    session_name=self.session_var.get()
                )
                self._recorder.start()
                self._active_recording = True

            self.root.after(0, lambda: self._update_status("Recording started...", recording=True))
            self.root.after(0, lambda: self._update_button_states(recording=True))

            logger.info("Recording started successfully.")

        except Exception as e:
            self.root.after(0, lambda: self._safe_messagebox("error", "Recording Error", f"Failed to start recording: {e}"))
            logger.error(f"Recording start error: {e}", exc_info=True)
            self.root.after(0, lambda: self._update_status("Error starting recording.", error=True))
            self.root.after(0, lambda: self._update_button_states(idle=True))

    
    def _stop_recording(self):
        """Stop the recording process."""
        with self._recorder_lock:
            if self._recorder and self._active_recording:
                try:
                    self.root.after(0, lambda: self._update_status("Stopping recording...", info=True))
                    # Get session folder before stopping
                    session_folder = self._recorder.session_folder
                    self._recorder.stop()

                    self._active_recording = False
                    self._scheduled = False 

                    # Use captured session_folder
                    if session_folder and not self._is_closing:
                        self.root.after(0, lambda: self._safe_messagebox("info", "Recording Complete", 
                                                                        f"Recording saved to: {session_folder}"))
                        logger.info(f"Recording stopped, saved to: {session_folder}")
                        self.root.after(0, lambda: self._update_status(f"Recording saved to: {session_folder}", info=True))
                    else:
                        logger.warning("Recording stopped but no session folder was available")
                        self.root.after(0, lambda: self._update_status("Recording stopped (no save location available)", warning=True))

                except Exception as e:
                    self.root.after(0, lambda: self._safe_messagebox("error", "Error", f"Failed to stop recording: {e}"))
                    logger.error(f"Recording stop error: {e}", exc_info=True)
                    self.root.after(0, lambda: self._update_status("Error stopping recording.", error=True))
                finally:
                    self._recorder = None
                    if not self._is_closing:
                        self.root.after(0, lambda: self._update_button_states(idle=True))
            else:
                logger.warning("Attempted to stop recording when none was active.")
                if not self._is_closing:
                    self.root.after(0, lambda: self._update_button_states(idle=True))


    def _run_scheduled_recording(self, duration_seconds: int):
        """Run for a specified duration for scheduled recordings."""
        try:
            start_time = time.time()
            self.root.after(0, lambda: self._update_status("Recording in progress...", recording=True))
            while (time.time() - start_time) < duration_seconds and not self._stop_flag.is_set() and not self._is_closing:
                elapsed_sec = int(time.time() - start_time)
                remaining_sec = duration_seconds - elapsed_sec
                
                elapsed_min = elapsed_sec // 60
                elapsed_sec_display = elapsed_sec % 60
                
                remaining_min = remaining_sec // 60
                remaining_sec_display = remaining_sec % 60

                status_text = (f"Recording: {elapsed_min:02d}:{elapsed_sec_display:02d} (Remaining: {remaining_min:02d}:{remaining_sec_display:02d}) "
                               f"/ Duration: {duration_seconds // 60:02d}m")
                self.root.after(0, lambda s=status_text: self._update_status(s, recording=True))
                time.sleep(1)

            if not self._stop_flag.is_set() and not self._is_closing:
                self._stop_recording() # Automatically stop if duration is reached
            else:
                self.root.after(0, lambda: self._update_status("Scheduled recording stopped manually or cancelled.", error=True))
                self.root.after(0, lambda: self._update_button_states(idle=True))

        except Exception as e:
            logger.error(f"Scheduled recording runtime error: {e}", exc_info=True)
            self.root.after(0, lambda: self._safe_messagebox("error", "Recording Error", f"An error occurred during scheduled recording: {e}"))
        finally:
            self._scheduled = False
            self._active_recording = False
            self._recording_thread = None
            self.root.after(0, lambda: self._update_button_states(idle=True))
            if not self._is_closing:
                self.root.after(0, lambda: self._update_status("Recording process finalized.", info=True))


    def _user_stop_recording(self):
        """Handle user clicking stop button."""
        if self._active_recording or self._scheduled:
            logger.info("User clicked stop button.")
            self._stop_flag.set() # Signal to stop
            if self._active_recording:
                self._stop_recording()
            # If scheduled, the thread will handle stopping and updating state
        self.root.after(0, lambda: self._update_button_states(idle=True)) # Ensure buttons are reset quickly


    def _handle_cancel(self):
        """Handle cancel button click for scheduled recordings."""
        logger.info("User clicked cancel button.")
        if self._scheduled and not self._active_recording:
            self._stop_flag.set()  # Signal to the waiting thread to stop
            self._scheduled = False
            self.root.after(0, lambda: self._update_status("Scheduled recording cancelled.", info=True))
            self.root.after(0, lambda: self._update_button_states(idle=True))
        else:
            logger.warning("Cancel button clicked but no active schedule to cancel.")


    def _update_button_states(self, idle: bool = False, recording: bool = False, scheduled: bool = False):
        """
        Thread-safe button state updater.
        idle: GUI is ready, no recording/scheduling
        recording: A recording is actively happening
        scheduled: A recording is scheduled but not yet active
        """
        def update():
            if not self.root.winfo_exists(): # Check if the window still exists
                return
            
            if idle:
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                self.cancel_btn.config(state="disabled")
            elif recording:
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
                self.cancel_btn.config(state="disabled")
            elif scheduled:
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="disabled")
                self.cancel_btn.config(state="normal")
            
        if self.root and self.root.winfo_exists():
            try:
                self.root.after_idle(update) # Use after_idle to run as soon as possible on main thread
            except tk.TclError: # Catch errors if window is already destroyed
                pass


    def _update_status(self, text: str, info: bool = False, warning: bool = False, error: bool = False, recording: bool = False):
        """
        Thread-safe status label updater.
        Changes color based on status type.
        """
        def update():
            if not self.root.winfo_exists():
                return
            self.status_label.config(text=text)
            if info:
                self.status_label.config(foreground="green")
            elif warning:
                self.status_label.config(foreground="orange")
            elif error:
                self.status_label.config(foreground="red")
            elif recording:
                self.status_label.config(foreground="blue")
            else:
                self.status_label.config(foreground="black")
        
        if self.root and self.root.winfo_exists():
            try:
                self.root.after_idle(update)
            except tk.TclError:
                pass


    def _safe_messagebox(self, msg_type: str, title: str, message: str):
        """
        Thread-safe messagebox display.
        This function should only be called via self.root.after() if from a background thread.
        However, for window close, direct calls are made.
        """
        def show_on_main_thread():
            if not self.root.winfo_exists():
                return
            if msg_type == "info":
                messagebox.showinfo(title, message)
            elif msg_type == "warning":
                messagebox.showwarning(title, message)
            elif msg_type == "error":
                messagebox.showerror(title, message)
        
        # If not called from the main thread, schedule it.
        # This is primarily for errors occurring in background threads.
        # For _on_window_close, direct calls are made so this path won't be taken.
        if threading.current_thread() != threading.main_thread():
             if self.root and self.root.winfo_exists():
                try:
                    self.root.after_idle(show_on_main_thread)
                except tk.TclError:
                    pass
        else:
            show_on_main_thread()


    def _on_window_close(self):
        """Handle window close event - safely save recording if active."""
        self._is_closing = True  # Set flag immediately

        if self._active_recording or self._scheduled:
            response = messagebox.askyesnocancel(
                "Recording in Progress",
                "A recording is in progress or scheduled.\n\n"
                "Do you want to stop and save the recording before closing?\n"
                "Yes: Stop and save recording, then close.\n"
                "No: Close without saving (recording will be lost).\n"
                "Cancel: Keep the application open."
            )

            if response is True:  # User chose to save recording
                logger.info("User chose to save recording before closing")
                self._stop_flag.set()  # Signal to stop threads

                self._update_status("Saving recording before closing...", info=True)
                
                # Wait for recording thread to finish (with timeout)
                if self._recording_thread and self._recording_thread.is_alive():
                    self._recording_thread.join(timeout=5) # Wait for max 5 seconds

                # Explicitly stop recorder if it's still active (might have been missed by thread join)
                with self._recorder_lock:
                    if self._recorder and self._active_recording:
                        try:
                            # CRITICAL FIX: Capture session_folder BEFORE stopping
                            saved_folder = self._recorder.session_folder
                            self._recorder.stop(save_output=True)  # Explicitly save output
                            logger.info(f"Recording stopped and saved to: {saved_folder}")
                            if self.root.winfo_exists():  # Check if root still exists
                                messagebox.showinfo("Recording Complete", f"Recording saved to: {saved_folder}")
                        except Exception as e:
                            logger.error(f"Error saving recording during close: {e}", exc_info=True)
                            if self.root.winfo_exists():
                                messagebox.showerror("Error Saving", f"Failed to save recording during close: {e}")
                        finally:
                            self._recorder = None
                            self._active_recording = False
                
            elif response is False:  # User chose to close without saving
                logger.info("User chose to close without saving")
                self._stop_flag.set()
                with self._recorder_lock:
                    if self._recorder and self._active_recording:
                        try:
                            self._recorder.stop(save_output=False)  # Explicitly don't save output
                            logger.info("Recording stopped without saving during close.")
                        except Exception as e:
                            logger.error(f"Error during unsaved stop on close: {e}", exc_info=True)
                        finally:
                            self._recorder = None
                            self._active_recording = False
            
            if self._recording_thread and self._recording_thread.is_alive():
                self._recording_thread.join(timeout=1)
            
            # Only proceed with close if user didn't cancel
            if response is not None:
                # Perform final cleanup and destroy the window
                self._cleanup_on_exit()
                self.root.destroy()
            else:
                # User cancelled - reset flag and keep window open
                self._is_closing = False
                return
        else:
            # No recording active - just close normally
            self._cleanup_on_exit()
            self.root.destroy()


    def _cleanup_on_exit(self):
        """Clean up resources before exit."""
        try:
            if self._active_recording or self._scheduled:
                self._stop_flag.set()
                with self._recorder_lock:
                    if self._recorder:
                        try:
                            self._recorder.stop(save_output=False)
                        except:
                            pass
                        finally:
                            self._recorder = None
                            self._active_recording = False
                            self._scheduled = False

            if self._recording_thread and self._recording_thread.is_alive():
                self._recording_thread.join(timeout=1)

            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def launch_gui():
    """Launch the RecordMyMeeting GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    root = tk.Tk()
    app = RecordMyMeetingGUI(root)
    try:
        root.mainloop()
    except Exception as e:
        logger.error(f"GUI mainloop error: {e}", exc_info=True)
    finally:
        logger.info("GUI application terminated")


if __name__ == "__main__":
    launch_gui()