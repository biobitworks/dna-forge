# Technical guide: Find the Right Patients pipeline

Research demo on **synthetic** pathology reports and de-identified slides. No medical claims; not for clinical decisions.

## Layout
```
data/                     unzipped challenge packs (pack_reports, pack_slides, thumbnails, embeddings), sibling of hack/
hack/
  parse_reports.py        header + FINAL DIAGNOSIS parser (both layouts); self-check 9010/9010 exact vs train labels
  criteria_engine.py      structured row + the 30 criteria as explicit, readable filters (each returns matched-field evidence)
  a_criteria.py           Task A: train P/R/F1, test submission, evidence + table for the app
  slides_common.py        manifest/embedding loaders
  c1_organ.py             C1 grid: kNN / logistic regression x single / concatenated models, 5x5 stratified CV + leave-one-supplier-out
  c1_tune.py              C1 supplier-centring + C sweep (exploration, prints only)
  c1_predict.py           C1 final model -> submission + probabilities
  c2_similar.py           C2: cosine + C1 re-rank; CV P@1/5/10 grid; submission + neighbour lists
  bridge.py               PoC: criteria engine on the 57 slide reports -> C2 candidate slides
  score_baseline.py       keyword baseline scored per criterion on train
  make_app_data.py        precomputes app/data/*.json + square thumbnails
  export_html.py          static single-file fallback -> out/static_demo.html (template: static_template.html)
  app/                    the deployable Streamlit app (app.py, data/, thumbs/, requirements.txt, Dockerfile)
  out/                    submissions and all intermediate results
  run_all.sh              whole pipeline, CPU only, ~3 min
```
Each script reads only the data and earlier `out/` files, so teammates can run stages independently.

## Run
```
pip install -r requirements.txt
./run_all.sh
cd app && streamlit run app.py
```

## Submission files (in out/)
- `submission_criteria.json`: Task A, `{"cXX": {"ids": [...], "count": n}}` for all 30 criteria
- `submission_slides_organ.csv`: C1, 67 held-out slides
- `submission_slides_similar.csv`: C2, 67 x 10 rows, no self-hits

## Deploy
**Streamlit Community Cloud** (free): push `hack/app/` to a GitHub repo (≈15 MB with data and thumbs) → share.streamlit.io → New app → pick the repo, main file `app.py` (or `app/app.py` if you push the whole hack/ folder; Cloud reads the requirements.txt next to the main file) → Deploy.

**Hugging Face Spaces**: New Space → SDK **Docker** → upload the contents of `hack/app/` (Dockerfile included; it serves on port 7860).
`git lfs` is not needed: no file is over 10 MB, but check `data/reports.json` if you add the train prose.

**Offline fallback**: open `out/static_demo.html` in any browser (self-contained, 5.8 MB, no server).

## After 4:00 PM
Score the three files on the challenge page, then write `out/official_scores.json`, e.g.
`{"A_mean_f1": 0.0, "C1_accuracy": 0.0, "C2_p@1": 0.0, "C2_p@5": 0.0, "C2_p@10": 0.0}`, and rerun `python3 make_app_data.py` to show them in the Evaluation tab.
