import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

from recordmymeeting import __version__
from recordmymeeting.core import RecordMyMeeting
from recordmymeeting.device_manager import print_all_devices, auto_detect_devices


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
        description="RecordMyMeeting - Effortlessly capture audio and screen.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Examples (for help message)
    parser.epilog = """Examples:
  # List available devices
  recordmymeeting --list-devices

  # Record ONLY your microphone (for interviews - compliance friendly)
  recordmymeeting --source mic --session-name "Interview_Google_Round1" --duration 60

  # Schedule mic-only recording for 2:30 PM
  recordmymeeting --source mic --schedule 14:30 --duration 60

  # Record only screen (for demos/tutorials)
  recordmymeeting --source screen --duration 30

  # Record everything (mic + speaker + screen)
  recordmymeeting --source all --output ./my_recordings --duration 30

  # With specific microphone device
  recordmymeeting --source mic --mic-device 2 --session-name "Interview"

  # Launch GUI for interactive control
  recordmymeeting-gui
"""

    parser.add_argument('--version', action='version', version=f'RecordMyMeeting {__version__}')
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

    # Advanced options
    adv_group = parser.add_argument_group('Advanced Options')
    adv_group.add_argument('--fps', type=int, default=10, help='Video frames per second (default: 10)')
    adv_group.add_argument('--audio-rate', type=int, default=44100, help='Audio sample rate in Hz (default: 44100)')

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Handle --list-devices
    if args.list_devices:
        print_all_devices()
        sys.exit(0)

    # Determine recording sources based on --source flag
    record_mic = False
    record_speaker = False
    record_screen = False

    if args.source:
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
    else:
        # Default: record mic only (most common use case)
        record_mic = True
        logging.info("Recording mode: Microphone only (default)")

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
        if 'mic' in detected and detected['mic']:
            mic_index = detected['mic']['index']
            logging.info(f"Using microphone: {detected['mic']['name']} (Index: {mic_index})")
        else:
            logging.error("No microphone detected. Use --list-devices to see available devices.")
            sys.exit(1)

    # Only detect speaker if we're recording speaker
    if record_speaker and speaker_index is None:
        logging.info("Auto-detecting speaker device...")
        detected = auto_detect_devices()
        if 'speaker' in detected and detected['speaker']:
            speaker_index = detected['speaker']['index']
            logging.info(f"Using speaker: {detected['speaker']['name']} (Index: {speaker_index})")
        else:
            logging.warning("No speaker detected. Disabling speaker recording.")
            record_speaker = False

    # Create Recorder
    try:
        recorder = RecordMyMeeting(
            output_dir=args.output,
            mic_index=mic_index if record_mic else None,
            speaker_index=speaker_index if record_speaker else None,
            record_mic=record_mic,
            record_speaker=record_speaker,
            record_screen=record_screen,
            session_name=args.session_name,
            video_fps=args.fps,
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
            if target_time < datetime.now():
                target_time += timedelta(days=1)
            
            logging.info(f"Recording scheduled for {target_time.strftime('%Y-%m-%d %H:%M')}")
            
            while datetime.now() < target_time:
                time_to_wait = target_time - datetime.now()
                time.sleep(1)
            print("\n")
            
        except ValueError:
            logging.error("Invalid schedule format. Use HH:MM (24-hour format).")
            sys.exit(1)

    # Start recording
    logging.info("Starting recording...")
    recorder.start()

    # Record for specified duration or wait for Ctrl+C
    try:
        if args.duration:
            for i in range(args.duration * 60):
                elapsed_min = i // 60
                elapsed_sec = i % 60
                print(f"Recording... {elapsed_min:02d}:{elapsed_sec:02d} / {args.duration:02d}:00", end='\r', flush=True)
                time.sleep(1)
            print("\n")
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
