# Data requests: what we still need from teammates

The stack and the fractal custody graph (FCG) already cover the four Biobase
packs and the HistAI gynaecology metadata. This page lists what is missing. If
you have one of these, or can get it, take it: comment on issue #14 with the
item number so nobody else does the same work.

## How any new data plugs in

1. **Terms first.** Before you download anything, find its licence or terms and
   add a row to the source table in `DATA_POLICY.md`. If the terms forbid our
   use, stop.
2. **Data stays off git.** Put the files on the machines (ask Byron where).
   Never put them in git, issues or chat. `scripts/check_no_data.py` and the
   data-guard CI reject data files.
3. **Hash it in.** Add the files to a custody ingest manifest
   (`custody/ingest-<date>-<source>.json`, the same shape as
   `ingest-2026-11-14-histai-meta.json`), so each file is a custody object in
   the FCG. Commit only the manifest.
4. **Make it a model, or a feature for one.** Anything that changes C1 or C2
   enters through `docs/MODEL_CONTRACT.md`. That means the shared folds,
   `oof_organ.csv` and `heldout_organ.csv` (and `*_similar.csv` if you have
   them), and a `record.json` that hashes every input and output. Data that is
   not tied to a slide (for example symptom tables) goes in as a separate
   model with its own record, and the write-up reports it on its own.
5. **No held-out lookups.** Do not label held-out slides and do not search
   outside sources for them (`DATA_POLICY.md`).

Deadline for anything that goes into the stack: **2:30 PM PT**. After that,
data can still go into the write-up and the FCG, but not into the submitted
files.

## Missing items

| # | What | Why we need it | Current state | How it plugs in |
|---|---|---|---|---|
| D1 | **Hackathon rules and the data agreement** (DNA Forge / Biobase) | R9 in `docs/SUBMISSION.md`. We cannot show compliance without them. | Not in any pack or knowledge-base link (#7) | Link or summarise them in `DATA_POLICY.md`. Don't commit the text if the terms forbid it. |
| D2 | **Kaggle endometriosis dataset licence** | R8. The dataset is listed but not cleared. | The License tab needs a Kaggle login (#7) | Record the licence in `DATA_POLICY.md`, then hash the CSV into an ingest manifest |
| D3 | **More PCOS cases** | HistAI gyn has only 4 PCOS slides out of 3,927 matched, which is too few to learn from | `custody/histai-gyn.json` (CC-BY-NC-4.0) | Public, licensed PCOS slides or embeddings. They go into an ingest manifest, then into a contribution under the model contract. |
| D4 | **Clinical and symptom features beyond the 6 Kaggle columns** | A different signal from the slide embeddings, which is what makes a contribution orthogonal | Only the 6 Kaggle columns; Synthea (MITRE) is in hand but not used | Public tables or Synthea generator configs. Commit the config only and hash the generated output. It goes in as a separate model with its own record. |
| D5 | **Proteomics from MassIVE** | An orthogonal molecular signal for the write-up and later work | None chosen | Record each dataset's MSV id and licence in `DATA_POLICY.md`. Commit only the dataset ids and hashes. |
| D6 | **New slide or tile embeddings** (UNI, CONCH or similar, licence permitting) over the 0.5 um tile pack | A different model family from the four provided vectors (#9) | Not started | A new `slide-vectors.json` on the machines, hashed into the run record `outputs`, then a contract contribution |
| D7 | **Supplier or site metadata** for supplier-normalised vectors | To check for and remove supplier bias (#10) | Not started | A per-slide supplier table, hashed. Used only as a transform, never as a label. |
| D8 | **Licence check for any model you add** | Same rule as the slide models (`embeddings/models.json`) | Ongoing | A row in `DATA_POLICY.md` before use |

## What we do not need

- More copies of the Biobase packs. Use the hashed ones on the machines.
- Labels for held-out slides from any source. That breaks `DATA_POLICY.md`.
