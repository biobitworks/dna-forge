"""Score the keyword baseline on train (per criterion) for the Evaluation tab."""
import json
from a_criteria import prf
from parse_reports import DATA
ans = json.load(open(DATA / "criteria_train_answers.json")); b = json.load(open("out/baseline_on_train.json"))
sc = {c: dict(zip(["precision", "recall", "f1", "tp"], prf(set(b[c]), set(ans[c])))) for c in ans}
m = sum(v["f1"] for v in sc.values()) / 30; print("baseline mean train F1", round(m, 4))
json.dump({"scores": sc, "mean_f1": m}, open("out/baseline_train_scores.json", "w"))
