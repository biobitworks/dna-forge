from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import hashlib
import pytest
p=Path(__file__).resolve().parents[1]/"scripts/verify_selected_submission.py"
spec=spec_from_file_location("submission_gate",p)
m=module_from_spec(spec);spec.loader.exec_module(m)
def test_valid_synthetic(tmp_path):
    b=b"header\nfake\n"
    (tmp_path/"test.csv").write_bytes(b)
    assert m.verify(tmp_path,{"test.csv":hashlib.sha256(b).hexdigest()})["test.csv"]["bytes"]==len(b)
def test_mismatch(tmp_path):
    (tmp_path/"test.csv").write_bytes(b"bad")
    with pytest.raises(ValueError,match="MISMATCH"):m.verify(tmp_path,{"test.csv":hashlib.sha256(b"good").hexdigest()})
def test_missing(tmp_path):
    with pytest.raises(FileNotFoundError):m.verify(tmp_path,{"x.csv":"0"*64})
def test_empty_expected(tmp_path):
    with pytest.raises(ValueError):m.verify(tmp_path,{})
def test_reject_symlink(tmp_path):
    p=tmp_path/"s.csv";p.write_bytes(b"fake")
    (tmp_path/"link.csv").symlink_to(p)
    with pytest.raises(FileNotFoundError):m.verify(tmp_path,{"link.csv":hashlib.sha256(b"fake").hexdigest()})
