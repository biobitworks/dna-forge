"""Task A: parse reports, apply 30 filters, score on train, write test submission + evidence."""
import json, sys
from pathlib import Path
from parse_reports import parse, load, DATA
import criteria_engine as CE

OUT = Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)

def build(path):
    rows = []
    for r in load(path):
        p = parse(r["report_text"]); rows.append((r["id"], CE.row(p)))
    return rows

def prf(pred, gold):
    tp = len(pred & gold); p = tp / len(pred) if pred else (1.0 if not gold else 0.0)
    rc = tp / len(gold) if gold else 1.0; f = 2 * p * rc / (p + rc) if p + rc else 0.0
    return p, rc, f, tp

def score(matches, answers):
    res = {}
    for cid in CE.FILTERS:
        pred = set(matches[cid]); gold = set(answers[cid])
        p, r, f, tp = prf(pred, gold); res[cid] = dict(precision=p, recall=r, f1=f, pred=len(pred), gold=len(gold), tp=tp)
    return res

if __name__ == "__main__":
    crit = {c["id"]: c["text"] for c in json.load(open(DATA / "criteria.json"))}
    train = build(DATA / "train.jsonl"); test = build(DATA / "test.jsonl")
    answers = json.load(open(DATA / "criteria_train_answers.json"))
    m_tr = CE.match_all(train); sc = score(m_tr, answers)
    for cid, s in sc.items():
        print(f"{cid} P={s['precision']:.3f} R={s['recall']:.3f} F1={s['f1']:.3f} pred={s['pred']} gold={s['gold']}  {crit[cid][:70]}")
    mean = sum(s["f1"] for s in sc.values()) / 30; print(f"MEAN TRAIN F1 = {mean:.4f}")
    m_te = CE.match_all(test)
    sub = {cid: {"ids": sorted(m_te[cid]), "count": len(m_te[cid])} for cid in CE.FILTERS}
    json.dump(sub, open(OUT / "submission_criteria.json", "w"), indent=1)
    json.dump({"train_scores": sc, "mean_train_f1": mean}, open(OUT / "a_train_scores.json", "w"), indent=1)
    # evidence + table for the app
    tab = {}
    for split, rows in (("train", train), ("test", test)):
        for rid, r in rows: tab[rid] = {**{k: v for k, v in r.items() if k != "fields"}, "split": split, "fields": r["fields"]}
    json.dump({"test": m_te, "train": m_tr}, open(OUT / "a_evidence.json", "w"))
    json.dump(tab, open(OUT / "a_table.json", "w"))
    print("test counts:", {k: v["count"] for k, v in sub.items()})
