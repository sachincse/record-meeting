import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

from . import __version__
from .core import RecordFlow
from .device_manager import print_devices, auto_detect_devices
from .gui_app import launch_gui


def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RecordFlow - Effortlessly capture audio and screen.",
        formatter_class=argparse.RawTextHelpFormatter  # For better help formatting
    )

    # Examples (for help message)
    parser.epilog = """Examples:
  # List available devices
  recordflow-cli --list-devices

  # Record ONLY your microphone (for interviews - compliance friendly)
  recordflow-cli --source mic --session-name "Interview_Google_Round1" --duration 60

  # Schedule mic-only recording for 2:30 PM
  recordflow-cli --source mic --schedule 14:30 --duration 60

  # Schedule mic-only recording for 2:30 PM (alternative simplified flag)
  recordflow-cli --mic-only --schedule 14:30 --duration 60

  # Record only screen (for demos/tutorials)
  recordflow-cli --source screen --duration 30

  # Record everything (mic + speaker + screen)
  recordflow-cli --source all --output ./my_recordings --duration 30

  # With specific microphone device
  recordflow-cli --source mic --mic-device 2 --session-name "Interview"

  # Launch GUI for interactive control
  recordflow-cli --gui
"""

    parser.add_argument('---version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    # Device management
    device_group = parser.add_argument_group('Device Management')
    device_group.add_argument('--list-devices', action='store_true', help='List all available audio devices and exit')
    device_group.add_argument('--mic-device', type=int, default=None, help='Microphone device index')
    device_group.add_argument('--speaker-device', type=int, default=None, help='Speaker device index')

    # Recording options
    rec_group = parser.add_argument_group('Recording Options')
    rec_group.add_argument('-o', '--output', type=str, default='./recordings', help='Output directory (default: ./recordings)')
    rec_group.add_argument('--session-name', type=str, default=None, help='Session name for recording folder')
    rec_group.add_argument('-d', '--duration', type=int, default=None, help='Recording duration in minutes')
    rec_group.add_argument('--schedule', type=str, default=None,
                           help='Schedule recording start time (24-hour format) HH:MM')

    # Source selection - simplified
    source_group = parser.add_argument_group('Recording Sources (Compliance-Friendly!)')
    source_group.add_argument('--source', type=str, choices=['mic', 'speaker', 'screen', 'all'],
                               help='what to record: mic (only your voice), speaker (system audio), screen (display), or all (mic + speaker + screen)')

    # Legacy options for backward compatibility (hidden from help)
    parser.add_argument('--no-mic', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--mic-only', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-speaker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--speaker-only', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--no-screen', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--screen-only', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--all', action='store_true', help=argparse.SUPPRESS)

    # Advanced options
    adv_group = parser.add_argument_group('Advanced Options')
    adv_group.add_argument('--fps', type=int, default=10, help='Video frames per second (default: 10)')
    adv_group.add_argument('--audio-rate', type=int, default=44100, help='Audio sample rate in Hz (default: 44100)')

    # GUI
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Handle --list-devices
    if args.list_devices:
        print_devices()
        sys.exit(0)

    # Launch GUI
    if args.gui:
        launch_gui()
        sys.exit(0)

    # Determine recording sources based on simplified --source flag
    record_mic = False
    record_speaker = False
    record_screen = False

    # Priority 1: Handle legacy exclusive flags first (--mic-only, --speaker-only, --screen-only)
    if args.mic_only:
        record_mic = True
        logging.info("Recording mode: Microphone only (compliance-friendly!)")
    elif args.speaker_only:
        record_speaker = True
        logging.info("Recording mode: Speaker/system audio only")
    elif args.screen_only:
        record_screen = True
        logging.info("Recording mode: Screen capture only")
    elif args.all:
        record_mic = True
        record_speaker = True
        record_screen = True
        logging.info("Recording mode: All sources (mic + speaker + screen)")
    # Priority 2: Handle new simplified --source flag
    elif args.source:
        if args.source == 'mic':
            record_mic = True
            logging.info("Recording mode: Microphone only (compliance-friendly!)")
        elif args.source == 'speaker':
            record_speaker = True
            logging.info("Recording mode: Speaker/system audio only")
        elif args.source == 'screen':
            record_screen = True
            logging.info("Recording mode: Screen capture only")
        elif args.source == 'all':
            record_mic = True
            record_speaker = True
            record_screen = True
            logging.info("Recording mode: All sources (mic + speaker + screen)")
    # Priority 3: Handle legacy boolean flags (--mic, --no-mic, etc.)
    else: # If no explicit --source or exclusive legacy flag, then check individual flags
        if not args.no_mic: # If --no-mic is NOT present, then record mic
            record_mic = True
        if not args.no_speaker: # If --no-speaker is NOT present, then record speaker
            record_speaker = True
        if not args.no_screen: # If --no-screen is NOT present, then record screen
            record_screen = True

    # Validate at least one source
    if not (record_mic or record_speaker or record_screen):
        logging.error("At least one recording source must be enabled")
        sys.exit(1)

    # Auto-detect devices only if needed
    mic_index = args.mic_device
    speaker_index = args.speaker_device

    # Only detect mic if we're recording mic
    if record_mic and mic_index is None:
        logging.info("Auto-detecting microphone device...")
        detected = auto_detect_devices()
        if 'mic' in detected:
            mic_index = detected['mic']['index']
            logging.info(f"Using microphone: {detected['mic']['name']} (Index: {mic_index})")
        else:
            logging.error("No microphone detected. Use --list-devices to see available devices.")
            sys.exit(1)

    # Only detect speaker if we're recording speaker
    if record_speaker and speaker_index is None:
        logging.info("Auto-detecting speaker device...")
        detected = auto_detect_devices()
        if 'speaker' in detected:
            speaker_index = detected['speaker']['index']
            logging.info(f"Using speaker: {detected['speaker']['name']} (Index: {speaker_index})")
        else:
            logging.warning("No speaker detected. Disabling speaker recording.")
            record_speaker = False # Disable speaker recording if not found

    # Create Recorder
    try:
        recorder = RecordFlow(
            output_dir=args.output,
            mic_index=mic_index if record_mic else None,
            speaker_index=speaker_index if record_speaker else None,
            record_screen=record_screen,
            session_name=args.session_name,
            fps=args.fps,
            audio_rate=args.audio_rate,
        )
    except Exception as e:
        logging.error(f"Failed to initialize recorder: {e}")
        sys.exit(1)

    # Handle scheduled recording
    if args.schedule:
        try:
            hour, minute = map(int, args.schedule.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time")
            
            target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time < datetime.now(): # If scheduled time is in the past, schedule for next day
                target_time += timedelta(days=1)
            
            logging.info(f"Recording scheduled for {target_time.strftime('%Y-%m-%d %H:%M')}")
            
            while datetime.now() < target_time:
                time_to_wait = target_time - datetime.now()
                # print(f"Waiting for {time_to_wait} until scheduled start...", end='\r', flush=True)
                time.sleep(1) # Check every second
            print("\n") # New line after waiting
            
        except ValueError:
            logging.error("Invalid schedule format. Use HH:MM (24-hour format).")
            sys.exit(1)

    # Start recording
    logging.info("Starting recording...")
    recorder.start()

    # Record for specified duration or wait for Ctrl+C
    try:
        if args.duration:
            for i in range(args.duration * 60): # args.duration is in minutes
                elapsed_min = i // 60
                elapsed_sec = i % 60
                print(f"Recording... {elapsed_min:02d}:{elapsed_sec:02d} / {args.duration:02d}:00", end='\r', flush=True)
                time.sleep(1)
            print("\n") # New line after recording
        else:
            logging.info("Recording. Press Ctrl+C to stop")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Recording interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred during recording: {e}")
    finally:
        # Stop recording
        logging.info("Stopping recording...")
        recorder.stop()
        logging.info(f"Recording saved to: {recorder.session_folder}")

if __name__ == '__main__':
    main()