from datetime import datetime,timezone,timedelta
from pathlib import Path
import importlib.util
import hashlib
import sys
from zoneinfo import ZoneInfo
import pytest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"scripts"))
spec=importlib.util.spec_from_file_location("prekey",HERE/"scripts/freeze_selected_submission.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_before_cutoff():
    assert m.clock_gate(datetime(2026,11,14,15,0,tzinfo=ZoneInfo("America/Los_Angeles"))).startswith("2026-11-14T23:00:00")
def test_at_cutoff_rejected():
    with pytest.raises(ValueError,match="cutoff"):
        m.clock_gate(datetime(2026,11,14,16,0,tzinfo=ZoneInfo("America/Los_Angeles")))
def test_after_cutoff_rejected():
    with pytest.raises(ValueError,match="cutoff"):
        m.clock_gate(datetime(2026,11,14,16,1,tzinfo=ZoneInfo("America/Los_Angeles")))
def test_naive_rejected():
    with pytest.raises(ValueError,match="timezone"):
        m.clock_gate(datetime(2026,11,14,15,0))
def test_wrong_day_rejected():
    with pytest.raises(ValueError,match="wrong day"):
        m.clock_gate(datetime(2026,11,13,15,0,tzinfo=ZoneInfo("America/Los_Angeles")))
def test_append_only(tmp_path):
    for item in ("snapshot","private.json","public.json"):
        (tmp_path/item).touch()
    with pytest.raises(FileExistsError):
        m.freeze(tmp_path,tmp_path/"snapshot",tmp_path/"private.json",tmp_path/"public.json",
                 "a"*40,datetime(2026,11,14,15,0,tzinfo=ZoneInfo("America/Los_Angeles")))
