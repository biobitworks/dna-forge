import json

from dnaforge import histai as H
from dnaforge import fcg as F


def rec(case, dx, icd, concl="", age=40, gender="f", micro=""):
    return {"diagnosis": dx, "conclusion": concl, "diff_diagnostic": "", "grossing": "", "micro_protocol": micro,
            "icd10": icd, "age": age, "gender": gender, "case_mapping": case, "additional_info": "",
            "specialization": "Gynecologic"}


RECS = [
    rec("histai/x/case_1", "Endometriosis of the ovary.", "N80.1"),
    rec("histai/x/case_1", "Endometriosis of the ovary.", "N80.1"),                      # exact dup
    rec("histai/x/case_2", "Endometriosis  of the ovary", "N80.1"),                      # content dup
    rec("histai/x/case_3", "Polycystic ovarian morphology.", "E28.2"),
    rec("histai/x/case_4", "Simple endometrial hyperplasia without atypia.", "N85.0",
        micro="Endometrial scraping (curettage)."),
    rec("histai/x/case_5", "Prostate adenocarcinoma.", "C61", gender="m"),
    rec("histai/x/case_6", "Leiomyoma of the uterus.", "D25.9"),
]


def test_tags():
    assert H.tags(RECS[0]) == ["endometriosis", "uterus"]
    assert H.tags(RECS[3]) == ["pcos"]
    assert H.tags(RECS[4]) == ["diagnostic", "pre-endometriosis", "uterus"]
    assert H.tags(RECS[5]) == []
    assert "uterus" in H.tags(RECS[6])


def test_dedupe_and_graph(tmp_path):
    sel = H.select(RECS)
    assert sel["stats"]["dup_exact"] == 1 and sel["stats"]["dup_content"] == 1
    assert sel["stats"]["clusters"] == 4
    endo = [c for c in sel["clusters"] if "endometriosis" in c["tags"]][0]
    assert endo["cases"] == ["histai/x/case_1", "histai/x/case_2"]
    g = H.graph(sel, "0" * 64)
    assert {m["identity"]["name"] for m in g["members"]} >= {"histai-gyn/pcos", "histai-gyn/uterus"}
    # order of input does not change the root
    g2 = H.graph(H.select(list(reversed(RECS))), "0" * 64)
    assert g2["identity"]["root"] == g["identity"]["root"]
    pub = json.dumps(H.public(g, sel))
    assert "Endometriosis" not in pub          # no free text in public files
    prov = H.to_prov(g, sel)
    assert any(i.get("@id") == H.ICD_URI + "N80.1" for i in prov["@graph"])
    assert "Endometriosis" not in json.dumps(prov)


def test_cli(tmp_path):
    src = tmp_path / "metadata.json"
    src.write_text(json.dumps(RECS))
    H.main([str(src), "--out", str(tmp_path / "local"), "--custody", str(tmp_path / "custody")])
    assert (tmp_path / "local/histai-gyn.jsonl").read_text().count("\n") == 4
    assert json.loads((tmp_path / "custody/histai-gyn.json").read_text())["stats"]["matched"] == 6
