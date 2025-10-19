
def test_cli_imports():
    """Test that CLI module can be imported."""
    from recordmymeeting.cli import main
    assert main is not None

def test_core_imports():
    """Test that core module can be imported."""
    from recordmymeeting.core import RecordMyMeeting
    assert RecordMyMeeting is not None
