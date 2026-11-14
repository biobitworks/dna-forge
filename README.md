# dna-forge

DNA Forge AI x Biology Hackathon (November 14, 2026) entry for the Biobase
"Find the Right Patients" challenge.

See [WORKSTREAM.md](WORKSTREAM.md) for who is working on what, and
[DATA_POLICY.md](DATA_POLICY.md) for how challenge data is handled.

## Quick start (on the machine holding the data)

```
git clone https://github.com/biobitworks/dna-forge && cd dna-forge
# unzip the five biobase-challenge-*.zip packs into ~/dna-forge/biobase/<pack>/
python3 -m dnaforge ingest ~/Downloads/biobase-challenge-*.zip   # custody/ingest-<date>.json
python3 -m dnaforge verify custody/ingest-<date>.json             # re-hash, prints "intact"
python3 -m dnaforge eval                                          # LOO + supplier-holdout per model
python3 -m dnaforge submit --models gigapath                      # C1/C2 CSVs + runs/<id>/record.json
```

Modules: `dnaforge.data` (slides, tiles, embeddings), `dnaforge.custody`
(hashing, ingest manifests, run records), `dnaforge.transforms` (tile
preprocessing and a PyTorch dataset), `dnaforge.probes` (k-NN, pooling,
C1/C2 metrics). Tests: `python3 -m pytest tests`.
