
# Quickstart

## Install

```bash
pip install -e .
```

## Device Verification

```bash
recordflow --list-devices
```

## Three Ways to Record

### 1. Python SDK
```python
from recordflow import RecordFlow
rec = RecordFlow()
rec.start()
# ...
rec.stop()
```

### 2. CLI
```bash
recordflow --mic --duration 5 --session-name "Test"
```

### 3. GUI
```bash
recordflow-gui
```

## Common Use Cases
- Interview recording
- Compliance-friendly audio capture
- Screen recording for demos

