
import os
from recordmymeeting.core import RecordMyMeeting

def test_recordmymeeting_init():
    """Test that RecordMyMeeting can be initialized without hardware."""
    # Initialize without starting (no hardware required)
    rec = RecordMyMeeting(
        output_dir="./test_recordings",
        session_name="test_session",
        record_mic=False,
        record_speaker=False,
        record_screen=False
    )
    assert rec is not None
    assert rec.session_name == "test_session"
    assert rec.record_mic is False
    assert rec.record_speaker is False
    assert rec.record_screen is False
