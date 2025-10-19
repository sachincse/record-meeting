import pyaudio
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def classify_device(device_name: str) -> Dict[str, bool]:
    """
    Classify device type based on name patterns.

    Args:
        device_name: Name of the audio device

    Returns:
        dict: Classification flags for device type
    """
    name_lower = device_name.lower()
    return {
        'is_headphone': any(keyword in name_lower for keyword in ['headphone', 'headset', 'airpods', 'earbuds', 'beats', 'bluetooth', 'wireless', 'usb audio']),
        'is_builtin': any(keyword in name_lower for keyword in ['built-in', 'internal', 'integrated']),
        'is_external': any(keyword in name_lower for keyword in ['external', 'usb', 'thunderbolt', 'displayport']),
        'is_virtual': any(keyword in name_lower for keyword in ['loopback', 'virtual', 'aggregate', 'blackhole', 'soundflower']),
        'is_mic': any(keyword in name_lower for keyword in ['microphone', 'mic', 'input']),
        'is_speaker': any(keyword in name_lower for keyword in ['speaker', 'output', 'playback']),
    }


def get_device_priority(device: Dict) -> int:
    """
    Calculate device priority for auto-selection.
    Higher priority = better choice for recording.

    Args:
        device: Device information dictionary

    Returns:
        int: Priority score (higher is better)
    """
    priority = 0
    classification = classify_device(device['name'])

    # Prefer headphones/external devices for mic (better quality, isolation)
    if classification['is_headphone']:
        priority += 50
    elif classification['is_external']:
        priority += 20
    elif classification['is_builtin']:
        priority += 10

    # Avoid virtual devices for primary recording
    if classification['is_virtual']:
        priority -= 50

    # Prefer devices with more channels
    priority += min(device.get('channels', 0) * 2, 10)

    # Prefer standard sample rates
    default_sample_rate = device.get('default_sample_rate', 0)
    try:
        if int(default_sample_rate) in [44100, 48000]:
            priority += 5
    except Exception:
        # If default_sample_rate is missing or not an int-convertible value, ignore
        pass

    return priority


def list_audio_devices() -> Dict[str, List[Dict]]:
    """
    List all available audio devices.

    Returns:
        Dict: Dictionary with 'microphones' and 'speakers' lists containing device info

    Example:
        >>> print(devices['microphones'])
        [{'index': 0, 'name': 'Built-in Microphone', 'channels': 2, ...}]
    """
    p = pyaudio.PyAudio()
    microphones = []
    speakers = []

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        device_data = {
            'index': i,
            'name': info['name'],
            'channels': info['maxInputChannels'] if info['maxInputChannels'] > 0 else info['maxOutputChannels'],
            'default_sample_rate': info['defaultSampleRate'],
            'host_api': p.get_host_api_info_by_index(info['hostApi'])['name']
        }

        # Devices with input channels can be used for recording
        if info['maxInputChannels'] > 0:
            microphones.append(device_data)

        # Devices with output channels can be used as speakers
        if info['maxOutputChannels'] > 0:
            speakers.append(device_data)

    p.terminate()

    return {
        'microphones': microphones,
        'speakers': speakers,
        'all_devices': microphones + speakers
    }


def get_default_devices() -> Dict[str, Optional[int]]:
    """
    Get system default audio devices.

    Returns:
        Dict: Dictionary with 'mic' and 'speaker' default device indices
    """
    p = pyaudio.PyAudio()
    mic_index = None
    speaker_index = None

    try:
        default_input = p.get_default_input_device_info()
        mic_index = default_input['index']
    except Exception as e:
        logger.warning(f"Could not get default input device: {e}")

    try:
        default_output = p.get_default_output_device_info()
        speaker_index = default_output['index']
    except Exception as e:
        logger.warning(f"Could not get default output device: {e}")
    finally:
        p.terminate()

    return {
        'mic': mic_index,
        'speaker': speaker_index
    }


def test_device(device_index: int, duration: float = 0.5) -> bool:
    """
    Test if a device is working by attempting a short recording/playback.

    Args:
        device_index: Index of the device to test
        duration: Test duration in seconds (default: 0.5)

    Returns:
        bool: True if device is working, False otherwise
    """
    p = pyaudio.PyAudio()
    try:
        # Try to open a stream with the device
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input_device_index=device_index,
                        input=True,
                        frames_per_buffer=1024)

        # Try to read some data
        for _ in range(0, int(44100 / 1024 * duration)):
            data = stream.read(1024, exception_on_overflow=False)
            if not data:
                return False

        stream.stop_stream()
        stream.close()
        return True
    except Exception as e:
        logger.debug(f"Device {device_index} test failed: {e}")
        return False
    finally:
        p.terminate()


def auto_detect_devices() -> Dict[str, Optional[Dict]]:
    """
    Automatically detect working audio devices with smart prioritization.
    Handles headphones, built-in devices, and external audio interfaces.

    Returns:
        Dict: Dictionary with 'mic' and 'speaker' device information
    """
    p = pyaudio.PyAudio()
    devices = {}
    
    try:
        # First try to find default devices
        try:
            default_input = p.get_default_input_device_info()
            default_output = p.get_default_host_api_info().get('defaultOutputDevice')
            
            if default_input:
                # Test default input device
                try:
                    test_stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        input_device_index=int(default_input['index']),
                        frames_per_buffer=1024
                    )
                    test_stream.stop_stream()
                    test_stream.close()
                    
                    devices['mic'] = {
                        'index': int(default_input['index']),
                        'name': default_input['name'],
                        'channels': int(default_input.get('maxInputChannels', 1))
                    }
                    logger.info(f"Default microphone detected: {default_input['name']}")
                except Exception as e:
                    logger.warning(f"Default microphone test failed: {e}")
            
            if default_output and default_output >= 0:
                output_info = p.get_device_info_by_index(default_output)
                # Test output device for input capability (loopback)
                try:
                    test_stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        input_device_index=default_output,
                        frames_per_buffer=1024
                    )
                    test_stream.stop_stream()
                    test_stream.close()
                    
                    devices['speaker'] = {
                        'index': default_output,
                        'name': output_info['name'],
                        'channels': int(output_info.get('maxInputChannels', 1))
                    }
                    logger.info(f"Default speaker detected: {output_info['name']}")
                except Exception as e:
                    logger.warning(f"Default speaker test failed: {e}")
                    
        except Exception as e:
            logger.warning(f"Error getting default devices: {e}")
            
        # If default devices not found or failed, scan all devices
        if not devices.get('mic') or not devices.get('speaker'):
            all_devices = list_audio_devices()
            
            # Find best microphone if not already set
            if not devices.get('mic') and all_devices.get('microphones'):
                candidates = sorted(all_devices['microphones'], 
                                 key=get_device_priority, 
                                 reverse=True)
                for device in candidates:
                    try:
                        test_stream = p.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=44100,
                            input=True,
                            input_device_index=device['index'],
                            frames_per_buffer=1024
                        )
                        test_stream.stop_stream()
                        test_stream.close()
                        
                        devices['mic'] = {
                            'index': device['index'],
                            'name': device['name'],
                            'channels': int(device.get('channels', 1))
                        }
                        logger.info(f"Best microphone found: {device['name']}")
                        break
                    except Exception as e:
                        logger.debug(f"Failed to test microphone {device['name']}: {e}")
                        continue
            
            # Find best speaker if not already set
            if not devices.get('speaker') and all_devices.get('speakers'):
                candidates = sorted(all_devices['speakers'], 
                                 key=get_device_priority, 
                                 reverse=True)
                for device in candidates:
                    try:
                        # For Windows, try to find WASAPI loopback device
                        if 'wasapi' in device['host_api'].lower():
                            test_stream = p.open(
                                format=pyaudio.paInt16,
                                channels=1,
                                rate=44100,
                                input=True,
                                input_device_index=device['index'],
                                frames_per_buffer=1024
                            )
                            test_stream.stop_stream()
                            test_stream.close()
                            
                            devices['speaker'] = {
                                'index': device['index'],
                                'name': device['name'],
                                'channels': int(device.get('channels', 1)),
                                'is_loopback': True
                            }
                            logger.info(f"Found WASAPI loopback device: {device['name']}")
                            break
                        # For other platforms or as fallback
                        elif 'output' in device['name'].lower() or 'speaker' in device['name'].lower():
                            test_stream = p.open(
                                format=pyaudio.paInt16,
                                channels=1,
                                rate=44100,
                                input=True,
                                input_device_index=device['index'],
                                frames_per_buffer=1024
                            )
                            test_stream.stop_stream()
                            test_stream.close()
                            
                            devices['speaker'] = {
                                'index': device['index'],
                                'name': device['name'],
                                'channels': int(device.get('channels', 1))
                            }
                            logger.info(f"Found speaker device: {device['name']}")
                            break
                    except Exception as e:
                        logger.debug(f"Failed to test speaker {device['name']}: {e}")
                        continue
                    
    except Exception as e:
        logger.error(f"Error during device detection: {e}")
    finally:
        try:
            p.terminate()
        except:
            pass
        
    return devices


def print_all_devices():
    """
    Print all available devices in a formatted way with classifications.
    """
    devices = list_audio_devices()

    print("\n" + "=" * 80)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 80 + "\n")

    if devices['microphones']:
        print("MICROPHONES:")
        print("-" * 15)
        for dev in devices['microphones']:
            classification = classify_device(dev['name'])
            tags = []
            if classification['is_headphone']:
                tags.append("Headphone")
            if classification['is_builtin']:
                tags.append("Built-in")
            if classification['is_external']:
                tags.append("External")
            if classification['is_virtual']:
                tags.append("Virtual/Loopback")

            tag_str = f" ({', '.join(tags)})" if tags else ""
            print(f"  [{dev['index']}] {dev['name']}{tag_str}")
            print(f"    Type: {'Input'}")
            print(f"    Channels: {dev['channels']}, Sample Rate: {int(dev['default_sample_rate'])} Hz")
        print("\n")
    else:
        print("No microphone devices found.\n")

    if devices['speakers']:
        print("SPEAKERS/PLAYBACK DEVICES:")
        print("-" * 25)
        for dev in devices['speakers']:
            classification = classify_device(dev['name'])
            tags = []
            if classification['is_headphone']:
                tags.append("Headphone")
            if classification['is_builtin']:
                tags.append("Built-in")
            if classification['is_external']:
                tags.append("External")
            if classification['is_virtual']:
                tags.append("Virtual/Loopback")

            tag_str = f" ({', '.join(tags)})" if tags else ""
            print(f"  [{dev['index']}] {dev['name']}{tag_str}")
            print(f"    Type: {'Output'}")
            print(f"    Channels: {dev['channels']}, Sample Rate: {int(dev['default_sample_rate'])} Hz")
        print("\n")
    else:
        print("No speaker devices found.\n")

    print("=" * 80)
    print("AUTO-DETECTED WORKING DEVICES (Smart Priority Selection)")
    print("=" * 80 + "\n")

    working = auto_detect_devices()
    if working.get('mic'):
        mic_classification = classify_device(working['mic']['name'])
        device_type = ""
        if mic_classification['is_headphone']:
            device_type = "Headphone Microphone"
        elif mic_classification['is_external']:
            device_type = "External Microphone"
        elif mic_classification['is_builtin']:
            device_type = "Built-in Microphone"
        elif mic_classification['is_virtual']:
            device_type = "Virtual Microphone"
        else:
            device_type = "Microphone"

        print(f"  Working Microphone: {working['mic']['name']} ({device_type})")
        print(f"    Index: {working['mic']['index']}, Channels: {working['mic']['channels']}\n")
    else:
        print("  No working microphone detected.")

    if working.get('speaker'):
        speaker_classification = classify_device(working['speaker']['name'])
        device_type = ""
        if speaker_classification['is_headphone']:
            device_type = "Headphone Speaker"
        elif speaker_classification['is_external']:
            device_type = "External Speaker"
        elif speaker_classification['is_builtin']:
            device_type = "Built-in Speaker"
        elif speaker_classification['is_virtual']:
            device_type = "Virtual/Loopback Speaker"
        else:
            device_type = "Speaker"

        print(f"  Working Speaker: {working['speaker']['name']} ({device_type})")
        print(f"    Index: {working['speaker']['index']}, Channels: {working['speaker']['channels']}\n")
    else:
        print("  No working speaker detected.")
    print("=" * 80 + "\n")


# Alias for backward compatibility
print_devices = print_all_devices


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print_all_devices()
