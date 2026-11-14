# DNA Forge × Biobase: Find the Right Patients

**2026-11-14 | Research prototype | Not for clinical use**

We built an interpretable search engine for synthetic pathology reports,
an organ classifier and similar-slide retrieval pipeline using supplied
pretrained pathology embeddings, and a Fractal Custody Graph (FCO/FCG)
for tracing source data through computations to selected outputs.

**For teammate review:**
[Model/training handoff](docs/MODEL_TRAINING_HANDOFF_20261114.md) |
[Presentation script](docs/PRESENTATION_REVIEW_20261114.md) |
[Submission table](docs/SUBMISSION.md) |
[Two-machine exact output receipts](docs/evidence/20261114_enssvm_crossnode_verified.json).

## Workflow from data to submission

~~~mermaid
flowchart TD
    A["5 organizer ZIP packs, licensed local source"] --> B["SHA-256 custody ingest and source FCO"]
    B --> R["9,010 labeled + 979 test reports"]
    B --> S["263 slide manifest and frozen image vectors"]
    R --> P["Parse diagnosis fields, 30 eligibility criteria"]
    P --> T["Task A JSON"]
    S --> F["190 organ-labeled slides and shared five-fold split"]
    F --> M["Train small ens-SVM on supplied GigaPath + H-optimus vectors"]
    M --> V["OOF, supplier checks, LOMO and negative model results"]
    V --> C["67 held-out organ labels and similar-slide rankings"]
    T --> G["Run receipts: input, method, output digest"]
    C --> G
    G --> H["Typed FCG / PROV-O custody projection"]
    H --> O["Three private candidate files and read-only hash gate"]
    O --> Q{"Official answer key released after 4 PM PT?"}
    Q -->|No| N["Do not access hidden labels"]
    Q -->|Yes| E["Score unchanged frozen predictions"]
    E --> U["Human submits files; retain organizer receipt"]
~~~

### 1. Source and permission gate

The five organizer-provided packs are reports, slides, thumbnails,
tiles and 20x tiles. The report pack contains 9,010 labeled training
reports, 979 unlabeled test reports, 30 criteria and train answers.
The slide manifest includes 263 slides, with 190 usable
organ-group training labels, six additional unlabeled-organ
non-held-out slides and 67 held-out slides.

Four pretrained vector families are supplied: Prov-GigaPath,
H-optimus-0, BiomedCLIP and DINOv2. We did NOT pretrain any of their
base weights. The public repo contains source code and safe digests,
not slide vectors, patient text, images or training answer keys.
Challenge data terms and redistribution permission remain unverified;
see [DATA_POLICY.md](DATA_POLICY.md) and issue #7.

### 2. Build typed evidence and train

The report pipeline in dnaforge/reports.py parses diagnosis fields
and applies 30 authored eligibility predicates. It has no fitted
model weights. Train-derived mean F1 was 1.000, but criteria were
developed against all training labels, so this is **not independent
generalization evidence**. Three of seven independent synthetic
paraphrase challenges failed. Hidden-key F1: NOT_COMPUTED.

For slides, dnaforge/models.py fits lightweight SVMs on supplied
GigaPath and H-optimus feature vectors, using shared stratified
five-fold cross-validation. The selected ens-SVM produced C1 organ
and C2 ranked similarity candidates. Alternative kNN, logistic
regression, attention MIL, stacking, model sweeps and LOMO ablations
were evaluated; some were weaker, and supplier-held-out performance
was lower than ordinary within-supplier validation.

### 3. Reproduce on MagicPro and MagicStudio

Independent runs on both Macs used source code at
dda6c509815e0437171b15b0a76c6c64ee8856ae, Python 3.9.6,
NumPy 2.0.2, scikit-learn 1.6.1 and SciPy 1.13.1. The inputs,
five-fold assignments, model configuration and **all five output
SHA-256 digests matched exactly**. Both new run records had clean
code status. This supports computational reproducibility, not
clinical validity or a causally proven graph-derived accuracy gain.

A prior candidate record had code.dirty = true. The predecessor
was preserved; the two clean model runs are successors.
[Read the complete custody and failure analysis.](docs/PI_PM_CLAUDE_RECOVERY_CROSSNODE_20261114.md)

### 4. Bind each result to the custody graph

The evidence relationship is:

    source bytes → source/observation FCO → typed FCG relationship →
    model/transform run → output digest → claim → presentation artifact

The public FCG declared 23 member hashes and 153 graph edges.
The member Merkle root recomputed to
0ce023dc527748224c98a1fa4af7e3f62612d500f1f0520e68f6fe94f3a303e5.
Hash equality establishes identity, not scientific truth; graph edges
do not establish causality. No verified signing or MMR commitment
is claimed.

### 5. Preserve the selected submission bytes

The authoritative team candidate is local to MagicPro:

    ~/dna-forge/SUBMISSION-FINAL/

Run the read-only identity check on that machine:

    python3 scripts/verify_selected_submission.py \
      --directory ~/dna-forge/SUBMISSION-FINAL/

| Task | Selected file | SHA-256 |
|---|---|---|
| A criteria | submission_criteria.json | 1604ae1557ffad8e39c671a193fec113653984f2e8bf090791f5a15b62d88345 |
| C1 organ | submission_slides_organ.csv | 8a69914d27c707c8a61694c8d8123f2139141cd5b79ac358193dda5da4cf7356 |
| C2 similar | submission_slides_similar.csv | ed38172b0075b0415fcce2866a3c68d55a1214e578d0ddc97c19c070fb90d423 |

Identity was verified, but no independent timestamped pre-4 PM freeze
receipt, official hidden score or organizer submission is asserted.
Never overwrite these files or upload them to the public GitHub repo.

### 6. Score after 4 PM and obtain organizer receipt

The team target is a 3:30 PM Pacific frozen candidate, **before**
the 4 PM official key release. Only after the release may the
unchanged predictions be evaluated. Record metrics and source-key
provenance as new evidence rather than revising prior receipts.
A human teammate must submit by the announced 5 PM deadline and
record the actual confirmation. This has NOT been verified here.

## Current scores: keep development separate from official

| Task | Development evidence | Organizer-reported baseline | Limitation |
|---|---:|---:|---|
| Reports A | mean F1 1.000 on train-derived folds | keyword F1 ~0.27 | Rule-development leakage risk |
| C1 organ | OOF accuracy 0.8632 | GigaPath ~0.70 | Not official hidden accuracy or a controlled matched-split comparison |
| C2 similar | OOF P@1 / P@5 / P@10: 0.868 / 0.829 / 0.800 | P@1 ~0.80 | Development ranking |
| Patient selector demo | separate reported CV C1 ~0.82 | ~0.70 | Different model/evaluation, do not average results |
| Endometriosis symptoms | separate CV AUC ~0.655 | Not a challenge baseline | External enrichment with unresolved license |

**What we actually trained:** small SVM classifiers, experimental
logistic regression/stacking and attention-MIL heads. We did NOT
train or fine-tune Prov-GigaPath, H-optimus, BiomedCLIP or DINOv2.
No pretrained or fitted binary model weights are in GitHub.
Teammates refit small models from authorized local embeddings.
[Detailed model inventory and negative results.](docs/MODEL_TRAINING_HANDOFF_20261114.md)

## What teammates can pull and what must stay local

| Asset | MagicPro | MagicStudio | GitHub main |
|---|---|---|---|
| All five official unpacked Biobase packs | Present at ~/dna-forge/biobase | Full pack mirror NOT_VERIFIED | Not included |
| Reports training, test and criteria | Present under reports/pack_reports | Original ZIP available; unpacked parity NOT_VERIFIED | Not included |
| Slide manifest and four derived vectors | Present | Present in ~/projects/private/biobase-20261114/dnaforge-node | Digest metadata only |
| Full tiles and 20x images | Present locally | Full mirror NOT_VERIFIED | Not included |
| Model, report parser and FCG source | Available | Available in clone | MERGED |
| Exact two-node verification receipts | Present | Present | MERGED (safe summaries) |
| Three selected candidate outputs | SUBMISSION-FINAL | Not the chosen upload copy | Digests only |
| Patient selector demo app source | Available | Pullable | MERGED |
| Offline generated demo tables and predictions | Restricted local storage | Not assumed | Intentionally excluded |

The teammate can pull all **merged code and verification protocols**,
but not the official data packs or frozen predictions from GitHub.
Access to those remains subject to the organizers' data agreement.

## Reproduce the pipeline on authorized local input

### A. Install and verify the code

    git clone https://github.com/biobitworks/dna-forge.git
    cd dna-forge
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[ml,dev]'
    python -m pytest -q tests
    python scripts/check_no_data.py

The original exact replay pinned specific numerical library
versions; installing newer versions may change output bytes.

### B. Set licensed data paths on MagicPro

    export ROOT="$HOME/dna-forge/biobase"
    export REPORT_PACK="$ROOT/reports/pack_reports"
    export RUNS="$HOME/projects/private/biobase-20261114/new-teammate-run"
    mkdir -p "$RUNS"

Required slide inputs:

    $ROOT/slides/pack_slides/slides_manifest.json
    $ROOT/tiles/tilepack/embeddings/gigapath/slide-vectors.json
    $ROOT/tiles/tilepack/embeddings/hoptimus/slide-vectors.json

Task A additionally needs train.jsonl, test.jsonl, criteria.json
and criteria_train_answers.json under REPORT_PACK.
On MagicStudio use the separate verified vector-only root for
ens-SVM; full tile MIL and report pack parity are NOT_VERIFIED.

### C. Recompute folds, fit and write NEW run receipts

    python -m dnaforge --root "$ROOT" folds \
      --out custody/local/folds.json \
      --hash-out custody/local/folds.sha256
    diff custody/folds.sha256 custody/local/folds.sha256
    python -m dnaforge --root "$ROOT" --runs "$RUNS" submit \
      --method ens-svm --alpha 3 \
      --folds custody/local/folds.json

Task A:

    python -m dnaforge.reports --pack "$REPORT_PACK" \
      --runs-dir "$RUNS"

Alternative model (requires PyTorch and local original tile vectors):

    python -m dnaforge.mil --root "$ROOT" \
      --model hoptimus --runs "$RUNS"

Further scripts: scripts/sweep.py, scripts/ablate.py,
scripts/check_submission.py and scripts/crossnode_receipts.py.
Use notebooks/05_crossnode_enssvm_replay.ipynb as a protocol;
its notebook cells are NOT_EXECUTED, although equivalent local
CLI experiments were EXECUTED on both Macs.

### D. Show the Patient selector demo

The separate Streamlit app source lives in:

    Patient selector/find_right_patients_code_and_app(1)/hack/

See the README and TECHNICAL documents inside that directory.
Run the scripts locally, using the authorized datasets, to
produce hack/out and then open its app. Generated HTML,
slide-ID-bearing predictions and tables are never public artifacts.

A prior direct main commit did include such derived data.
PR #24 removed them from the current Git tree and fixed the data
guard, but **historical Git exposure was NOT purged**.
Do not claim the repository was historically data-clean.

## Missing information and action owners

| Missing item | State | Next actor |
|---|---|---|
| Complete Biobase challenge rules/data agreement | UNKNOWN | Organizer/team; see issue #7 |
| Kaggle endometriosis dataset license | UNKNOWN | Data owner; separate from HistAI CC BY-NC |
| HistAI PCOS, follicle, immune and IHC labeled orthogonal data | NOT_ADMITTED | Scientific/data curator; do not blend without permissions |
| Official independent 4 PM scores | NOT_COMPUTED | Evaluation lead after key release |
| Team opt-in/Team ID and official submission receipt | NOT_VERIFIED | Human team member |
| Old public Git-history generated-data exposure | UNRESOLVED | Repo owner, licensing/privacy review |
| Supplier-domain independent validation and 20x training | DEFERRED | Issues #9 and #10 |

[DNAForge event listing](https://luma.com/xdzhu4tn) establishes the
event and general application rules, but it does not establish the
Biobase-specific data agreement or final upload terms.

### Presentation checklist

- Introduce source data, standard embeddings and *fitted small SVM*.
- Compare development metrics fairly, not as official hidden scores.
- Show five matching SHA-256 digests and the FCO/FCG trail.
- Explain that integrity, attribution and biological causality
  are separate proof levels.
- Retain negative results: supplier effects, failed paraphrase tests,
  unpromoted MIL/stacking and earlier dirty-run evidence.
- Do not show private slide identifiers or claim an upload occurred
  without an organizer receipt.
- Review linked [speaker notes](docs/PRESENTATION_REVIEW_20261114.md),
  [model contract](docs/MODEL_CONTRACT.md),
  [open data requests](docs/DATA_REQUESTS.md),
  [contributor workflow](CONTRIBUTING.md), and
  [Claude lane resume](docs/CLAUDE_RESUME_20261114.md).

**Claim ceiling:** exact-byte output reproducibility and auditable
provenance. Hidden-test accuracy, clinical usefulness, source
authorization, signing and MMR commitment require separate evidence.

### Exact observed cross-node numerical environment

For a reproducible comparison, on CPython 3.9.6 install the pinned
dependency versions used in both successful Mac executions:

    python -m pip install -r envs/biobase-enssvm-crossnode-20261114.txt
    python -m pip install -e '.[dev]'

This pins numerical package versions but cannot substitute for
source-data matching or an exact platform/wheel fingerprint. A newly
run model is a successor receipt, never a silent replacement of the
selected files.
