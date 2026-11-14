"""Synthetic fixtures only: no real slide or report ids."""
import csv, importlib.util, json
from pathlib import Path

spec = importlib.util.spec_from_file_location("cs", Path(__file__).parent.parent / "scripts" / "check_submission.py")
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)


def _fixture(tmp):
    slides = [{"id": f"L{i}", "organ": "Lung", "organGroup": "Lung"} for i in range(12)]
    slides += [{"id": f"H{i}", "heldout": True} for i in range(3)]
    man = tmp / "m.json"
    man.write_text(json.dumps({"slides": slides, "organGroupList": ["Lung", "Breast"], "organGroups": {"Bronchus and lung": "Lung"}}))
    organ = tmp / "organ.csv"
    with open(organ, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["slide_id", "organ"]); w.writerows([["H0", "lung"], ["H1", "Breast"], ["H2", "Bronchus and lung"]])
    sim = tmp / "similar.csv"
    with open(sim, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["query_slide_id", "rank", "result_slide_id"])
        for q in ("H0", "H1", "H2"):
            w.writerows([[q, k + 1, f"L{k}"] for k in range(10)])
    return man, organ, sim


def test_valid_passes(tmp_path):
    man, organ, sim = _fixture(tmp_path)
    assert cs.main(["--manifest", str(man), "--organ", str(organ), "--similar", str(sim)]) == 0


def test_broken_fails(tmp_path):
    man, organ, sim = _fixture(tmp_path)
    organ.write_text("slide_id,organ\nH0,lung\nH0,Lung\nH1,Pancreas\n")
    lines = sim.read_text().splitlines()
    lines.append("H0,11,H0")
    sim.write_text("\n".join(lines) + "\n")
    assert cs.main(["--manifest", str(man), "--organ", str(organ), "--similar", str(sim)]) == 1
    text = " ".join(cs.problems)
    for want in ("duplicate", "no row", "organ values", "self-match", "ranks"):
        assert want in text


def test_criteria(tmp_path):
    tmpl = tmp_path / "t.json"; tmpl.write_text(json.dumps({"c1": [], "c2": []}))
    test = tmp_path / "test.jsonl"; test.write_text("\n".join(json.dumps({"id": f"r{i}"}) for i in range(5)))
    sub = tmp_path / "s.json"; sub.write_text(json.dumps({"c1": ["r1", "r2"], "c2": []}))
    assert cs.main(["--criteria", str(sub), "--criteria-template", str(tmpl), "--reports-test", str(test)]) == 0
    sub.write_text(json.dumps({"c1": ["r1", "r1", "zz"]}))
    assert cs.main(["--criteria", str(sub), "--criteria-template", str(tmpl), "--reports-test", str(test)]) == 1
