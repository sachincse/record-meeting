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
import logging

from .device_manager import auto_detect_devices

logger = logging.getLogger(__name__)

# Try to import pyaudiowpatch for WASAPI loopback (Windows speaker capture)
_has_wpatch = False
try:
    import pyaudiowpatch as pyaudio_wp
    _has_wpatch = True
except ImportError:
    pyaudio_wp = None

class RecordMyMeeting:
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
                 channels: int = 1,
                 session_name: Optional[str] = None):
        """
        Initialize RecordMyMeeting.

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
            if 'mic' in detected and detected['mic']:
                self.mic_index = detected['mic']['index']
                logger.info(f"Using microphone: {detected['mic']['name']} (Index: {self.mic_index})")
            else:
                raise RuntimeError("No microphone detected. Use recordmymeeting --list-devices to see available devices.")

        # Speaker detection: prefer WASAPI loopback (pyaudiowpatch) on Windows
        self._use_loopback = False
        self._loopback_device = None
        self._loopback_sr = self.audio_rate
        self._loopback_ch = 2

        if self.record_speaker and self.speaker_index is None:
            logger.info("Auto-detecting speaker device...")

            # Strategy 1: WASAPI loopback via pyaudiowpatch (best on Windows)
            if _has_wpatch and sys.platform == 'win32':
                try:
                    p_wp = pyaudio_wp.PyAudio()
                    wasapi_info = p_wp.get_host_api_info_by_type(pyaudio_wp.paWASAPI)
                    default_output = p_wp.get_device_info_by_index(wasapi_info['defaultOutputDevice'])

                    for lb in p_wp.get_loopback_device_info_generator():
                        if default_output['name'] in lb['name']:
                            self._loopback_device = lb
                            break

                    if self._loopback_device:
                        self._use_loopback = True
                        self._loopback_sr = int(self._loopback_device['defaultSampleRate'])
                        self._loopback_ch = self._loopback_device['maxInputChannels']
                        logger.info(f"Using WASAPI loopback: {self._loopback_device['name']} "
                                    f"(ch={self._loopback_ch}, sr={self._loopback_sr})")
                    p_wp.terminate()
                except Exception as e:
                    logger.debug(f"WASAPI loopback detection failed: {e}")

            # Strategy 2: Fallback to standard PyAudio device detection
            if not self._use_loopback:
                detected = auto_detect_devices()
                if 'speaker' in detected and detected['speaker']:
                    self.speaker_index = detected['speaker']['index']
                    logger.info(f"Using speaker: {detected['speaker']['name']}")
                    try:
                        p = pyaudio.PyAudio()
                        device_info = p.get_device_info_by_index(self.speaker_index)
                        max_ch = int(device_info.get('maxInputChannels', 0))
                        if max_ch == 0:
                            raise Exception("Device has no input channels")
                        test_ch = min(self.channels, max_ch)
                        test_stream = p.open(
                            format=self.format, channels=test_ch,
                            rate=self.audio_rate, input=True,
                            input_device_index=self.speaker_index,
                            frames_per_buffer=self.frames_per_buffer
                        )
                        test_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                        test_stream.stop_stream()
                        test_stream.close()
                        p.terminate()
                        logger.info("Speaker recording test successful")
                    except Exception as e:
                        logger.warning(f"Speaker recording test failed: {e}")
                        logger.warning("No working speaker detected, disabling speaker recording.")
                        self.record_speaker = False
                else:
                    logger.warning("No working speaker detected, disabling speaker recording.")
                    self.record_speaker = False

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
        self.speaker_frames = []

        # Start recording threads
        if self.record_screen:
            self.video_thread = threading.Thread(target=self._record_screen, daemon=True)
            self.video_thread.start()
        if self.record_mic or self.record_speaker:
            self.audio_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.audio_thread.start()

        logger.info("Recording started")

    def stop(self, save_output: bool = True):
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
                monitor = sct.monitors[0]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
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

    def _start_loopback_capture(self):
        """Start WASAPI loopback capture for speaker audio in a callback stream."""
        if not (self._use_loopback and _has_wpatch and self._loopback_device):
            return

        try:
            self._loopback_pa = pyaudio_wp.PyAudio()
            lb = self._loopback_device

            def _loopback_callback(in_data, frame_count, time_info, status):
                if in_data and self.recording:
                    self.speaker_frames.append(in_data)
                return (None, pyaudio_wp.paContinue)

            self._loopback_stream = self._loopback_pa.open(
                format=pyaudio_wp.paInt16,
                channels=self._loopback_ch,
                rate=self._loopback_sr,
                input=True,
                input_device_index=lb['index'],
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=_loopback_callback,
            )
            logger.info(f"WASAPI loopback stream opened (callback mode)")
        except Exception as e:
            logger.error(f"Failed to open loopback stream: {e}")
            self._use_loopback = False

    def _stop_loopback_capture(self):
        """Stop WASAPI loopback capture."""
        if hasattr(self, '_loopback_stream') and self._loopback_stream:
            try:
                self._loopback_stream.stop_stream()
                self._loopback_stream.close()
            except:
                pass
        if hasattr(self, '_loopback_pa') and self._loopback_pa:
            try:
                self._loopback_pa.terminate()
            except:
                pass

    def _record_audio(self):
        """Record audio from mic and/or speaker in a separate thread with dynamic device switching."""
        p = pyaudio.PyAudio()
        mic_stream = None
        speaker_stream = None

        current_mic_index = self.mic_index
        last_device_check = time.time()
        device_check_interval = 2.0

        try:
            # Open microphone stream
            if self.record_mic:
                try:
                    device_info = p.get_device_info_by_index(self.mic_index)
                    max_channels = int(device_info.get('maxInputChannels', self.channels))
                    actual_channels = min(self.channels, max_channels)

                    mic_stream = p.open(
                        format=self.format, channels=actual_channels,
                        rate=self.audio_rate, input=True,
                        input_device_index=self.mic_index,
                        frames_per_buffer=self.frames_per_buffer
                    )
                    logger.info(f"Microphone stream opened (device {self.mic_index}, channels: {actual_channels})")
                except Exception as e:
                    logger.error(f"Failed to open microphone stream: {e}")
                    self.record_mic = False

            # Speaker: use WASAPI loopback if available, otherwise fallback
            if self.record_speaker and self._use_loopback:
                self._start_loopback_capture()
            elif self.record_speaker and self.speaker_index is not None:
                try:
                    device_info = p.get_device_info_by_index(self.speaker_index)
                    max_channels = int(device_info.get('maxInputChannels', 0))
                    if max_channels == 0:
                        raise Exception("Device has no input channels")
                    actual_channels = min(self.channels, max_channels)
                    speaker_stream = p.open(
                        format=self.format, channels=actual_channels,
                        rate=self.audio_rate, input=True,
                        input_device_index=self.speaker_index,
                        frames_per_buffer=self.frames_per_buffer
                    )
                    logger.info(f"Speaker stream opened (device {self.speaker_index})")
                except Exception as e:
                    logger.error(f"Failed to open speaker stream: {e}")
                    self.record_speaker = False

            # Recording loop — mic uses blocking read, speaker loopback uses callback
            while self.recording:
                # Check for mic device changes periodically
                current_time = time.time()
                if current_time - last_device_check >= device_check_interval:
                    last_device_check = current_time
                    try:
                        new_devices = auto_detect_devices()
                        if self.record_mic and mic_stream and new_devices.get('mic'):
                            new_mic_index = new_devices['mic'].get('index')
                            if new_mic_index is not None and new_mic_index != current_mic_index:
                                logger.info(f"Mic changed: {current_mic_index} -> {new_mic_index}")
                                try:
                                    mic_stream.stop_stream()
                                    mic_stream.close()
                                    device_info = p.get_device_info_by_index(new_mic_index)
                                    max_ch = int(device_info.get('maxInputChannels', self.channels))
                                    mic_stream = p.open(
                                        format=self.format, channels=min(self.channels, max_ch),
                                        rate=self.audio_rate, input=True,
                                        input_device_index=new_mic_index,
                                        frames_per_buffer=self.frames_per_buffer
                                    )
                                    current_mic_index = new_mic_index
                                    self.mic_index = new_mic_index
                                    logger.info(f"Switched to mic device {new_mic_index}")
                                except Exception as e:
                                    logger.error(f"Failed to switch mic: {e}")
                    except Exception as e:
                        logger.debug(f"Device check error: {e}")

                # Read mic (blocking)
                if self.record_mic and mic_stream:
                    try:
                        mic_data = mic_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                        self.audio_frames.append(mic_data)
                    except Exception as e:
                        logger.warning(f"Mic read error: {e}")
                        try:
                            mic_stream.stop_stream()
                            mic_stream.close()
                            device_info = p.get_device_info_by_index(current_mic_index)
                            max_ch = int(device_info.get('maxInputChannels', self.channels))
                            mic_stream = p.open(
                                format=self.format, channels=min(self.channels, max_ch),
                                rate=self.audio_rate, input=True,
                                input_device_index=current_mic_index,
                                frames_per_buffer=self.frames_per_buffer
                            )
                            logger.info("Mic stream recovered")
                        except Exception:
                            logger.error("Failed to recover mic stream")
                            break

                # Read speaker (only for non-loopback fallback path)
                if self.record_speaker and speaker_stream and not self._use_loopback:
                    try:
                        speaker_data = speaker_stream.read(self.frames_per_buffer, exception_on_overflow=False)
                        self.speaker_frames.append(speaker_data)
                    except Exception as e:
                        logger.warning(f"Speaker read error: {e}")
                        break

                time.sleep(0.001)

            logger.info("Audio recording completed")

        except Exception as e:
            logger.error(f"Error during audio recording: {e}")
        finally:
            if mic_stream:
                try:
                    mic_stream.stop_stream()
                    mic_stream.close()
                except:
                    pass
            if speaker_stream:
                try:
                    speaker_stream.stop_stream()
                    speaker_stream.close()
                except:
                    pass
            self._stop_loopback_capture()
            p.terminate()

    def _save_audio(self):
        """
        Save recorded audio to WAV files.
        BUG FIX #1: Split condition check to ensure files are created even with empty frames.
        """
        p = pyaudio.PyAudio()
        
        # Save microphone audio - FIXED: Split condition check
        if self.record_mic and self.mic_file:
            if self.audio_frames:
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
            else:
                logger.warning("Microphone was set to record, but no audio frames were captured.")

        # Save speaker audio
        if self.record_speaker and self.speaker_file:
            if self.speaker_frames:
                try:
                    # Use loopback params if WASAPI loopback was used
                    sp_ch = self._loopback_ch if self._use_loopback else self.channels
                    sp_sr = self._loopback_sr if self._use_loopback else self.audio_rate
                    wf = wave.open(self.speaker_file, 'wb')
                    wf.setnchannels(sp_ch)
                    wf.setsampwidth(p.get_sample_size(self.format))
                    wf.setframerate(sp_sr)
                    wf.writeframes(b''.join(self.speaker_frames))
                    wf.close()
                    logger.info(f"Speaker audio saved: {self.speaker_file}")
                except Exception as e:
                    logger.error(f"Error saving speaker audio: {e}")
            else:
                logger.warning("Speaker was set to record, but no audio frames were captured.")
        
        p.terminate()


    def _merge_audio(self):
        """Merge microphone and speaker audio into a single file.

        Handles different sample rates and channel counts by resampling
        the speaker audio to match the mic format before mixing.
        """
        if not (self.mic_file and self.speaker_file and self.merged_file):
            logger.warning("Cannot merge audio: missing file paths.")
            return

        try:
            with wave.open(self.mic_file, 'rb') as wf_mic:
                mic_params = wf_mic.getparams()
                mic_audio_data = wf_mic.readframes(wf_mic.getnframes())

            with wave.open(self.speaker_file, 'rb') as wf_speaker:
                speaker_params = wf_speaker.getparams()
                speaker_audio_data = wf_speaker.readframes(wf_speaker.getnframes())

            mic_np = np.frombuffer(mic_audio_data, dtype=np.int16)
            speaker_np = np.frombuffer(speaker_audio_data, dtype=np.int16)

            # Convert speaker to mono if mic is mono but speaker is stereo
            if speaker_params.nchannels > mic_params.nchannels:
                # Reshape to (n_frames, n_channels) and average
                speaker_np = speaker_np.reshape(-1, speaker_params.nchannels)
                speaker_np = speaker_np.mean(axis=1).astype(np.int16)

            # Resample speaker to mic sample rate if different
            if speaker_params.framerate != mic_params.framerate:
                ratio = mic_params.framerate / speaker_params.framerate
                new_len = int(len(speaker_np) * ratio)
                indices = np.linspace(0, len(speaker_np) - 1, new_len).astype(int)
                speaker_np = speaker_np[indices]

            # Truncate to same length
            min_samples = min(len(mic_np), len(speaker_np))
            mic_np = mic_np[:min_samples]
            speaker_np = speaker_np[:min_samples]

            # Mix (average to prevent clipping)
            merged_np = (mic_np.astype(np.int32) + speaker_np.astype(np.int32)) // 2
            merged_audio_data = merged_np.astype(np.int16).tobytes()

            with wave.open(self.merged_file, 'wb') as wf_merged:
                wf_merged.setnchannels(mic_params.nchannels)
                wf_merged.setsampwidth(mic_params.sampwidth)
                wf_merged.setframerate(mic_params.framerate)
                wf_merged.writeframes(merged_audio_data)

            logger.info(f"Merged audio saved: {self.merged_file}")

        except Exception as e:
            logger.error(f"Error merging audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
