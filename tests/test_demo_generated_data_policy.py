"""Synthetic-only path protection tests; no real slide IDs or outputs."""
from pathlib import Path
import importlib.util
p=Path(__file__).resolve().parents[1]/"scripts/check_no_data.py"
spec=importlib.util.spec_from_file_location("demo_data_guard",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def test_generated_out_blocked():
    assert mod.blocked_reason("Patient selector/any-demo/hack/out/a_table.json")
def test_submission_csv_blocked():
    assert mod.blocked_reason("Patient selector/submission_slides_organ.csv")
def test_submission_json_blocked():
    assert mod.blocked_reason("Patient selector/submission_criteria.json")
def test_static_demo_blocked():
    assert mod.blocked_reason("Patient selector/static_demo.html")
def test_demo_source_allowed():
    assert mod.blocked_reason("Patient selector/safe-demo/hack/criteria_engine.py") is None
