import os
import cv2
import sys
import numpy as np
import pyaudio
import wave
import threading
import time
from datetime import datetime
from typing import Optional
import mss
import audioread
import logging

from .device_manager import auto_detect_devices

logger = logging.getLogger(__name__)

class RecordFlow:
    """
    Main class for recording audio and screen.

    Attributes:
        output_dir: Directory where recordings will be saved
        mic_index: Microphone device index
        speaker_index: Speaker device index
        record_mic: Whether to record microphone
        record_speaker: Whether to record speaker/system audio
        record_screen: Whether to record screen
        video_fps: Video frames per second
        audio_rate: Audio sample rate
        channels: Number of audio channels (1=mono, 2=stereo)
        session_name: Optional session name for the recording folder
    """
    def __init__(self,
                 output_dir: str = "./recordings",
                 mic_index: Optional[int] = None,
                 speaker_index: Optional[int] = None,
                 record_mic: bool = True,
                 record_speaker: bool = True,
                 record_screen: bool = True,
                 video_fps: int = 10,
                 audio_rate: int = 44100,
                 channels: int = 1, # Keep 1 as default, but allow override
                 session_name: Optional[str] = None):
        """
        Initialize RecordFlow.

        Args:
            output_dir: Directory to save recordings
            mic_index: Microphone device index (auto-detect if None)
            speaker_index: Speaker device index (auto-detect if None)
            record_mic: Enable microphone recording
            record_speaker: Enable speaker recording
            record_screen: Enable screen recording
            video_fps: Video frames per second
            audio_rate: Audio sample rate in Hz
            channels: Number of audio channels (1=mono, 2=stereo)
            session_name: optional session name for the recording folder
        """
        self.output_dir = output_dir
        self.record_mic = record_mic
        self.record_speaker = record_speaker
        self.record_screen = record_screen
        self.video_fps = video_fps
        self.audio_rate = audio_rate
        self.channels = channels
        self.format = pyaudio.paInt16
        self.frames_per_buffer = 1024
        self.session_name = session_name

        # Auto-detect devices ONLY if needed
        self.mic_index = mic_index
        self.speaker_index = speaker_index

        # Only detect microphone if recording mic and not provided
        if self.record_mic and self.mic_index is None:
            logger.info("Auto-detecting microphone device...")
            detected = auto_detect_devices()
            if 'mic' in detected:
                self.mic_index = detected['mic']['index']
                logger.info(f"Using microphone: {detected['mic']['name']} (Index: {self.mic_index})")
            else:
                raise RuntimeError("No microphone detected. Use recordflow-cli --list-devices to see available devices.")

        # Only detect speaker if recording speaker and not provided
        if self.record_speaker and self.speaker_index is None:
            logger.info("Auto-detecting speaker device...")
            detected = auto_detect_devices()
            if 'speaker' in detected:
                self.speaker_index = detected['speaker']['index']
                logger.info(f"Using speaker: {detected['speaker']['name']}")
                
                # Test if we can actually record from this device
                try:
                    p = pyaudio.PyAudio()
                    test_stream = p.open(
                        format=self.format,
                        channels=1,
                        rate=self.audio_rate,
                        input=True,
                        input_device_index=self.speaker_index,
                        frames_per_buffer=self.frames_per_buffer
                    )
                    # Try to read some data to verify it works
                    test_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                    test_stream.stop_stream()
                    test_stream.close()
                    p.terminate()
                    logger.info("Speaker recording test successful")
                except Exception as e:
                    logger.warning(f"Speaker recording test failed: {e}")
                    logger.warning("No working speaker detected, disabling speaker recording.")
                    self.record_speaker = False  # Disable speaker recording if test fails
            else:
                logger.warning("No working speaker detected, disabling speaker recording.")
                self.record_speaker = False  # Disable speaker recording if not found

        # Recording state
        self.recording = False
        self.audio_frames = []
        self.speaker_frames = []

        # File paths (set when recording starts)
        self.session_folder = None
        self.video_file = None
        self.mic_file = None
        self.speaker_file = None
        self.merged_file = None

        # Threads
        self.video_thread = None
        self.audio_thread = None

    def _create_session_folder(self) -> str:
        """Create a timestamped session folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.session_name:
            folder_name = f"{self.session_name}_{timestamp}"
        else:
            folder_name = f"recording_{timestamp}"
        session_path = os.path.join(self.output_dir, folder_name)
        os.makedirs(session_path, exist_ok=True)
        return session_path

    def start(self):
        """
        Start recording immediately or at a scheduled time.
        """
        if self.recording:
            logger.warning("Recording already in progress")
            return

        self.session_folder = self._create_session_folder()

        # Set file paths
        if self.record_screen:
            self.video_file = os.path.join(self.session_folder, "screen.mp4")
        if self.record_mic:
            self.mic_file = os.path.join(self.session_folder, "microphone.wav")
        if self.record_speaker:
            self.speaker_file = os.path.join(self.session_folder, "speaker.wav")
        if self.record_mic and self.record_speaker:
            self.merged_file = os.path.join(self.session_folder, "merged.wav")

        self.recording = True
        self.audio_frames = []
        self.speaker_frames = [] # Reset frames for new recording

        # Start recording threads
        if self.record_screen:
            self.video_thread = threading.Thread(target=self._record_screen, daemon=True)
            self.video_thread.start()
        if self.record_mic or self.record_speaker:
            self.audio_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.audio_thread.start()

        logger.info("Recording started")

    def stop(self, save_output: bool = True): # Add save_output parameter
        """
        Stop recording and save files.
        Args:
            save_output: If False, recording data will be discarded.
        """
        if not self.recording:
            logger.warning("No recording in progress")
            return

        logger.info(f"Stopping recording (save_output={save_output})...")
        self.recording = False

        # Wait for threads to finish
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join()
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()

        # Save audio files ONLY if save_output is True
        if save_output:
            if self.record_mic or self.record_speaker:
                self._save_audio()

            # Merge audio if both sources recorded
            if self.record_mic and self.record_speaker:
                # Ensure both lists are populated before attempting merge
                if self.audio_frames and self.speaker_frames:
                    self._merge_audio()
                else:
                    logger.warning("Cannot merge audio: one or both audio streams were not recorded.")
            logger.info(f"Recording saved to: {self.session_folder}")
        else:
            logger.info("Recording stopped without saving output.")

        # Always clear frames regardless of saving
        self.audio_frames = []
        self.speaker_frames = []

        # Reset file paths (optional, but good practice for next recording)
        self.session_folder = None
        self.video_file = None
        self.mic_file = None
        self.speaker_file = None
        self.merged_file = None


    def get_status(self) -> dict:
        """
        Get current recording status.

        Returns:
            dict: Status information including recording state and file paths
        """
        return {
            'recording': self.recording,
            'session_folder': self.session_folder,
            'record_mic': self.record_mic,
            'record_speaker': self.record_speaker,
            'record_screen': self.record_screen,
            'mic_file': self.mic_file,
            'speaker_file': self.speaker_file,
            'video_file': self.video_file,
            'merged_file': self.merged_file,
        }

    def _record_screen(self):
        """
        Record screen in a separate thread.
        """
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0] # Capture primary monitor
                fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec
                # Ensure output directory exists before creating video file
                os.makedirs(self.session_folder, exist_ok=True)
                out = cv2.VideoWriter(self.video_file, fourcc, self.video_fps,
                                      (monitor["width"], monitor["height"]))

                next_frame_time = time.time()
                while self.recording:
                    img = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    out.write(frame)

                    # Control frame rate
                    next_frame_time += 1.0 / self.video_fps
                    sleep_time = next_frame_time - time.time()
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                out.release()
                logger.info("Screen recording completed")
        except Exception as e:
            logger.error(f"Error during screen recording: {e}")

    def _record_audio(self):
        """Record audio from mic and/or speaker in a separate thread."""
        p = pyaudio.PyAudio()
        mic_stream = None
        speaker_stream = None
        detected_devices = auto_detect_devices()  # Get current device info

        try:
            # Open microphone stream if recording mic
            if self.record_mic:
                try:
                    # Get device info to check supported channels
                    device_info = p.get_device_info_by_index(self.mic_index)
                    max_channels = int(device_info.get('maxInputChannels', self.channels))
                    actual_channels = min(self.channels, max_channels)
                    
                    mic_stream = p.open(
                        format=self.format,
                        channels=actual_channels,  # Use supported channel count
                        rate=self.audio_rate,
                        input=True,
                        input_device_index=self.mic_index,
                        frames_per_buffer=self.frames_per_buffer
                    )
                    logger.info(f"Microphone stream opened (device {self.mic_index}, channels: {actual_channels})")
                except Exception as e:
                    logger.error(f"Failed to open microphone stream: {e}")
                    self.record_mic = False  # Disable mic recording on error

            # Open speaker stream if recording speaker
            if self.record_speaker:
                try:
                    # If no speaker index provided, try to find one
                    if self.speaker_index is None and 'speaker' in detected_devices:
                        self.speaker_index = detected_devices['speaker']['index']
                        logger.info(f"Using detected speaker device: {detected_devices['speaker']['name']}")
                    
                    if self.speaker_index is not None:
                        device_info = p.get_device_info_by_index(self.speaker_index)
                        max_channels = int(device_info.get('maxInputChannels', self.channels))
                        actual_channels = min(self.channels, max_channels)

                        # Try to open as WASAPI loopback first if on Windows
                        try:
                            if 'wasapi' in device_info.get('hostApi', '').lower():
                                speaker_stream = p.open(
                                    format=self.format,
                                    channels=actual_channels,
                                    rate=self.audio_rate,
                                    input=True,
                                    input_device_index=self.speaker_index,
                                    frames_per_buffer=self.frames_per_buffer,
                                    as_loopback=True  # Enable WASAPI loopback
                                )
                            else:
                                raise Exception("Not a WASAPI device")
                        except Exception:
                            # Fallback to normal input mode
                            speaker_stream = p.open(
                                format=self.format,
                                channels=actual_channels,
                                rate=self.audio_rate,
                                input=True,
                                input_device_index=self.speaker_index,
                                frames_per_buffer=self.frames_per_buffer
                            )
                        
                        logger.info(f"Speaker stream opened (device {self.speaker_index}, channels: {actual_channels})")
                    else:
                        raise Exception("No valid speaker device found")
                        
                except Exception as e:
                    logger.error(f"Failed to open speaker stream: {e}")
                    self.record_speaker = False  # Disable speaker recording on error

            # Record audio frames
            while self.recording:
                if self.record_mic and mic_stream:
                    try:
                        mic_data = mic_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                        self.audio_frames.append(mic_data)
                    except Exception as e:
                        logger.warning(f"Mic read error: {e}")
                        break  # Exit loop on persistent errors

                if self.record_speaker and speaker_stream:
                    try:
                        speaker_data = speaker_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                        self.speaker_frames.append(speaker_data)
                    except Exception as e:
                        logger.warning(f"Speaker read error: {e}")
                        break  # Exit loop on persistent errors

                time.sleep(0.001)

            logger.info("Audio recording completed")

        except Exception as e:
            logger.error(f"Error during audio recording: {e}")
        finally:
            # Clean up streams
            if mic_stream:
                mic_stream.stop_stream()
                mic_stream.close()
            if speaker_stream:
                speaker_stream.stop_stream()
                speaker_stream.close()
            p.terminate()

    def _save_audio(self):
        """
        Save recorded audio to WAV files.
        """
        p = pyaudio.PyAudio() # Initialize PyAudio for wave file parameters
        
        # Save microphone audio
        if self.record_mic and self.mic_file and self.audio_frames:
            try:
                wf = wave.open(self.mic_file, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(self.audio_rate)
                wf.writeframes(b''.join(self.audio_frames))
                wf.close()
                logger.info(f"Microphone audio saved: {self.mic_file}")
            except Exception as e:
                logger.error(f"Error saving microphone audio: {e}")
        elif self.record_mic:
            logger.warning("Microphone was set to record, but no audio frames were captured or mic_file not set.")

        # Save speaker audio
        if self.record_speaker and self.speaker_file and self.speaker_frames:
            try:
                wf = wave.open(self.speaker_file, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(self.audio_rate)
                wf.writeframes(b''.join(self.speaker_frames))
                wf.close()
                logger.info(f"Speaker audio saved: {self.speaker_file}")
            except Exception as e:
                logger.error(f"Error saving speaker audio: {e}")
        elif self.record_speaker:
            logger.warning("Speaker was set to record, but no audio frames were captured or speaker_file not set.")
        
        p.terminate()


    def _merge_audio(self):
        """
        Merge microphone and speaker audio into a single file.
        """
        if not (self.mic_file and self.speaker_file and self.merged_file):
            logger.warning("Cannot merge audio: one or more required file paths are missing.")
            return

        try:
            # Ensure both have the same number of frames
            # This is a simplification; a more robust solution would pad or resample.
            # Here, we truncate to the minimum length.
            with audioread.audio_open(self.mic_file) as f_mic:
                mic_nframes = f_mic.frames
            with audioread.audio_open(self.speaker_file) as f_speaker:
                speaker_nframes = f_speaker.frames
            
            min_frames = min(mic_nframes, speaker_nframes)

            # Read audio data
            # Use wave module for precise frame control
            with wave.open(self.mic_file, 'rb') as wf_mic:
                mic_audio_data = wf_mic.readframes(min_frames)
                mic_params = wf_mic.getparams()

            with wave.open(self.speaker_file, 'rb') as wf_speaker:
                speaker_audio_data = wf_speaker.readframes(min_frames)
                speaker_params = wf_speaker.getparams()

            # Convert to numpy arrays for mixing
            # Assuming paInt16 which is signed 16-bit
            mic_np = np.frombuffer(mic_audio_data, dtype=np.int16)
            speaker_np = np.frombuffer(speaker_audio_data, dtype=np.int16)

            # Mix (simple average)
            merged_np = (mic_np + speaker_np) // 2
            merged_audio_data = merged_np.astype(np.int16).tobytes()

            # Write merged audio to file
            with wave.open(self.merged_file, 'wb') as wf_merged:
                wf_merged.setnchannels(mic_params.nchannels)
                wf_merged.setsampwidth(mic_params.sampwidth)
                wf_merged.setframerate(mic_params.framerate)
                wf_merged.writeframes(merged_audio_data)

            logger.info(f"Merged audio saved: {self.merged_file}")

        except Exception as e:
            logger.error(f"Error merging audio: {e}")