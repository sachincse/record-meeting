
from recordmymeeting import device_manager

def test_list_audio_devices():
    """Test that list_audio_devices returns a dict with expected keys."""
    devices = device_manager.list_audio_devices()
    assert isinstance(devices, dict)
    assert 'microphones' in devices
    assert 'speakers' in devices
    assert isinstance(devices['microphones'], list)
    assert isinstance(devices['speakers'], list)

def test_classify_device():
    """Test device classification logic."""
    # Test headphone classification
    result = device_manager.classify_device("USB Headset")
    assert result['is_headphone'] is True
    
    # Test built-in classification
    result = device_manager.classify_device("Built-in Microphone")
    assert result['is_builtin'] is True
    
    # Test virtual classification
    result = device_manager.classify_device("VB-Audio Virtual Cable")
    assert result['is_virtual'] is True

def test_get_device_priority():
    """Test device priority calculation."""
    # Headphone should have higher priority than built-in
    headphone = {'name': 'USB Headset', 'channels': 2, 'default_sample_rate': 44100}
    builtin = {'name': 'Built-in Microphone', 'channels': 1, 'default_sample_rate': 44100}
    
    headphone_priority = device_manager.get_device_priority(headphone)
    builtin_priority = device_manager.get_device_priority(builtin)
    
    assert headphone_priority > builtin_priority
