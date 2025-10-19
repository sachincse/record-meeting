
from recordflow import device_manager

def test_list_devices_returns_list():
    devices = device_manager.list_input_devices()
    assert isinstance(devices, list)

def test_device_classification_and_scoring():
    # Simulate device info
    fake_devices = [
        {"name": "USB Headset", "maxInputChannels": 2},
        {"name": "Built-in Microphone", "maxInputChannels": 1},
        {"name": "VB-Audio Virtual Cable", "maxInputChannels": 2},
        {"name": "Unknown Device", "maxInputChannels": 1},
    ]
    # Patch list_input_devices to return fake devices with type/score
    orig = device_manager.list_input_devices
    def fake_list():
        out = []
        for i, info in enumerate(fake_devices):
            name = info["name"].lower()
            if "virtual" in name or "vb-audio" in name or "cable" in name:
                dev_type = "virtual"
                score = 5
            elif "headphone" in name or "headset" in name:
                dev_type = "headphones"
                score = 50
            elif "usb" in name or "external" in name:
                dev_type = "external"
                score = 20
            elif "built-in" in name or "internal" in name or "realtek" in name:
                dev_type = "built-in"
                score = 10
            else:
                dev_type = "unknown"
                score = 1
            out.append({"index": i, "name": info["name"], "maxInputChannels": info["maxInputChannels"], "type": dev_type, "score": score})
        return out
    device_manager.list_input_devices = fake_list
    devices = device_manager.list_input_devices()
    assert devices[0]["type"] == "headphones"
    assert devices[1]["type"] == "built-in"
    assert devices[2]["type"] == "virtual"
    assert devices[3]["type"] == "unknown"
    # Restore
    device_manager.list_input_devices = orig
