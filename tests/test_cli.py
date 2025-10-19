
def test_cli_version():
    from recordflow.cli import parse_args
    args = parse_args(["--version"])
    assert args.version is True

def test_cli_schedule_and_duration():
    from recordflow.cli import parse_args
    args = parse_args(["--mic", "--schedule", "14:30", "--duration", "5"])
    assert args.mic is True
    assert args.schedule == "14:30"
    assert args.duration == 5
