"""Synthetic-only regression tests: private challenge data never required."""
import importlib.util
from pathlib import Path
import pytest

s=importlib.util.spec_from_file_location("crossnode_receipts",Path(__file__).parents[1]/"scripts/crossnode_receipts.py")
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)

def fixture(node):
    h=lambda n:format(n,"064x")
    return {"schema":M.SCHEMA,"node":node,"run":"synthetic-run","source_commit":h(1),
            "source_code_dirty":False,"method":"ens-svm","config_sha256":h(2),
            "input_sha256":{x:h(i+5) for i,x in enumerate(sorted(M.REQUIRED_INPUTS))},
            "output_sha256":{x:h(i+15) for i,x in enumerate(sorted(M.REQUIRED_OUTPUTS))},
            "output_bytes":{x:100+i for i,x in enumerate(sorted(M.REQUIRED_OUTPUTS))},
            "development_metrics":{"oof_acc":0.80,"oof_p@1":0.80,"oof_p@5":0.70,"oof_p@10":0.60},
            "runtime":{"python":"3.11"},"verified":"LOCAL_REHASH_PASS"}

def test_cross_node_equal():
    r=M.compare(fixture("magicPRObox"),fixture("magicSTUDIObox"))
    assert r["n_matching_outputs"]==5 and r["official_hidden_test_metrics"]=="NOT_COMPUTED"

def test_outputs_divergent_rejected():
    a,b=fixture("magicPRObox"),fixture("magicSTUDIObox")
    b["output_sha256"]["oof_organ.csv"]=format(987,"064x")
    with pytest.raises(ValueError,match="CROSS_MACHINE_MISMATCH"):M.compare(a,b)

def test_source_divergent_rejected():
    a,b=fixture("magicPRObox"),fixture("magicSTUDIObox")
    b["input_sha256"]["folds"]=format(981,"064x")
    with pytest.raises(ValueError,match="CROSS_MACHINE_MISMATCH"):M.compare(a,b)

def test_same_node_rejected():
    with pytest.raises(ValueError,match="same machine"):M.compare(fixture("magicPRObox"),fixture("magicPRObox"))

def test_dirty_code_rejected():
    a=fixture("magicPRObox");b=fixture("magicSTUDIObox")
    b["source_code_dirty"]=True
    with pytest.raises(ValueError,match="dirty code"):M.compare(a,b)

def test_public_projection_rejects_private_paths(tmp_path):
    with pytest.raises(ValueError,match="unsafe"):M.safe_write(tmp_path/"a.json",{"private":"/Users/example"})
    assert not (tmp_path/"a.json").exists()

def test_public_projection_append_only(tmp_path):
    f=tmp_path/"a.json";M.safe_write(f,{"value":"safe"})
    with pytest.raises(FileExistsError,match="append-only"):M.safe_write(f,{"value":"changed"})
