# Patient selector: generate restricted outputs locally

The teammate's source code in
find_right_patients_code_and_app(1)/hack/ is retained for independent review.
The executable app and model code are not pretrained weights.

All generated outputs under hack/out/, plus standalone submission JSON/CSV and
static_demo.html files, are restricted derived challenge data and must remain
on an authorized local machine. They are not distributed by GitHub.

The previous direct main commit 139c2c47f5897e4f937fa64029ff2d0e260f5cae
tracked generated files. This successor removes them from the current tree,
but **does not remove them from Git history or caches**. The repository owner
must assess license/privacy and history remediation separately.
Do not claim history or remote caches have been sanitized.

## Rebuild, restricted to authorized local data

Follow the existing hack/README.md and hack/TECHNICAL.md. Provide the official
source challenge packs locally; run hack/run_all.sh from the hack directory.
The run creates hack/out/ on the local machine. Preview the Streamlit app
with the generated files local; do not commit hack/out or the static export.

Use docs/SUBMISSION.md as the canonical submission mapping for the
dnaforge main pipeline. Outputs from the separate Patient selector app
must not silently replace the frozen ~/dna-forge/SUBMISSION-FINAL files.

Published candidate metrics and demo metrics use DIFFERENT development
pipelines and are not interchangeable. No official hidden evaluation or
clinical validation is established by either source tree alone.

Do not regenerate prediction files after the official pre-4PM freeze.
