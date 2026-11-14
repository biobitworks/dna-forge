#!/usr/bin/env bash
# Full pipeline, CPU only (~3 min). Data must be unzipped into ../data (pack_reports, pack_slides, thumbnails, embeddings).
set -euo pipefail; cd "$(dirname "$0")"
python3 parse_reports.py        # parser check: 9010/9010 exact
python3 a_criteria.py           # Task A -> out/submission_criteria.json
python3 c1_organ.py             # C1 model grid (CV) -> out/c1_cv_grid.json
python3 c1_predict.py           # C1 final -> out/submission_slides_organ.csv
python3 c2_similar.py           # C2 -> out/submission_slides_similar.csv
python3 bridge.py               # Bridge PoC -> out/bridge.json
python3 ../data/pack_reports/baseline_keyword.py ../data/pack_reports/train.jsonl ../data/pack_reports/criteria.json out/baseline_on_train.json
python3 score_baseline.py
python3 make_app_data.py && python3 export_html.py
