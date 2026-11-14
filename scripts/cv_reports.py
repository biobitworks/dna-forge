"""Cross-check reports task A beyond train F1.

The task-A system is a parser plus hand-written predicates: nothing is fitted, so k-fold CV on
train measures stability over subsets, not generalisation. The real risk is that the rules were
written while looking at train. Three checks address it:

  1. 5-fold split of train: mean F1 per fold (spread shows criteria that hinge on a few cases).
  2. Test parse coverage: every test report must yield an organ and exactly the field set that
     organ has in train (unknown or missing fields would silently drop matches).
  3. Count sanity: for each criterion, test matches vs the train rate times 979; flag a criterion
     whose test count falls outside a 3-sigma binomial band.

  python3 scripts/cv_reports.py --pack ~/dna-forge/biobase/reports/pack_reports [--runs runs]
"""
import argparse
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dnaforge import reports as R  # noqa: E402
from dnaforge.custody import RunRecord  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    pack = Path(a.pack).expanduser()
    inputs = [pack / f for f in ("train.jsonl", "test.jsonl", "criteria_train_answers.json", "criteria.json")]
    with RunRecord("reports-cv", config=vars(a), inputs=inputs, runs_dir=a.runs) as run:
        train = R.load_jsonl(pack / "train.jsonl")
        test = R.load_jsonl(pack / "test.jsonl")
        answers = json.loads((pack / "criteria_train_answers.json").read_text())
        tcases = [R.Case(r["report_text"], r["id"]) for r in train]
        ecases = [R.Case(r["report_text"], r["id"]) for r in test]

        # 1. k-fold stability
        idx = list(range(len(tcases)))
        random.Random(a.seed).shuffle(idx)
        folds = [idx[f::a.folds] for f in range(a.folds)]
        fold_f1, per_crit = [], defaultdict(list)
        for f in folds:
            cs = [tcases[i] for i in f]
            ids = {c.id for c in cs}
            ans = {k: [i for i in v if i in ids] for k, v in answers.items()}
            table, m, _ = R.evaluate(cs, ans)
            fold_f1.append(m)
            for cid, t in table.items():
                per_crit[cid].append(t["f1"])
        mean = sum(fold_f1) / len(fold_f1)
        sd = math.sqrt(sum((x - mean) ** 2 for x in fold_f1) / len(fold_f1))
        weak = {cid: min(v) for cid, v in per_crit.items() if min(v) < 1.0}
        run.metrics["kfold"] = {"folds": a.folds, "mean_f1": round(mean, 4), "sd": round(sd, 4),
                                "per_fold": [round(x, 4) for x in fold_f1], "criteria_below_1": weak}
        print(f"{a.folds}-fold train mean F1 {mean:.4f} ± {sd:.4f}; criteria with any fold < 1: {weak or 'none'}")

        # 2. test parse coverage
        fields_by_organ = defaultdict(Counter)
        for c in tcases:
            fields_by_organ[c.organ][frozenset(c.d)] += 1
        known = {o: set(fs) for o, fs in fields_by_organ.items()}
        no_organ = [c.id for c in ecases if not c.organ]
        unseen = [c.id for c in ecases if c.organ and frozenset(c.d) not in known.get(c.organ, set())]
        all_train_fields = {k for c in tcases for k in c.d}
        new_fields = Counter(k for c in ecases for k in c.d if k not in all_train_fields)
        run.metrics["test_parse"] = {"reports": len(ecases), "no_organ": len(no_organ),
                                     "unseen_field_set": len(unseen), "fields_not_in_train": dict(new_fields),
                                     "organs": dict(Counter(c.organ for c in ecases))}
        print(f"test parse: {len(ecases)} reports, {len(no_organ)} without organ, "
              f"{len(unseen)} with a field set never seen in train, new fields: {dict(new_fields) or 'none'}")

        # 3. count sanity
        tsel, esel = R.select(tcases), R.select(ecases)
        n_tr, n_te = len(tcases), len(ecases)
        flags, counts = {}, {}
        for cid in R.CRITERIA:
            p = len(tsel[cid]) / n_tr
            exp = p * n_te
            band = 3 * math.sqrt(max(n_te * p * (1 - p), 1e-9))
            got = len(esel[cid])
            counts[cid] = {"train": len(tsel[cid]), "test": got, "expected": round(exp, 1)}
            if abs(got - exp) > max(band, 2):
                flags[cid] = counts[cid]
        run.metrics["counts"] = counts
        run.metrics["count_flags"] = flags
        print(f"count check: {len(flags)} of {len(counts)} criteria outside 3 sigma: {flags or 'none'}")
    print(f"record: {run.dir / 'record.json'}")


if __name__ == "__main__":
    main()
