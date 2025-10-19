
import os
from recordflow.core import RecordFlow

def test_recordflow_start_stop(tmp_path):
    # Use a short session name and output dir
    outdir = tmp_path / "recordings"
    rec = RecordFlow(output_dir=str(outdir), session_name="test_session", record_mic=False, record_screen=False)
    rec.start()
    rec.stop()
    # Should create a session folder
    found = False
    for d in os.listdir(outdir):
        if "test_session" in d:
            found = True
    assert found
