"""Utility helpers for RecordMyMeeting"""
import os
from datetime import datetime


def make_session_dir(output_dir: str, session_name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    dirname = f"{session_name}_{ts}" if session_name else ts
    path = os.path.join(output_dir, dirname)
    os.makedirs(path, exist_ok=True)
    return path
