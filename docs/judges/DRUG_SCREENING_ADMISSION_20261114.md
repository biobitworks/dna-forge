# Drug-screening source admission is a separate experiment

**PROPOSED; not implemented in the current DAISY gene-perturbation chain.**

The inspected source config at
cloudmer-vcc-alpha-overnight-20261020/config/daisy_chain.yaml
identifies vcc_daisy_training with gene-perturbation metrics
(PDS/MSE/NMAE/FID/reach/Jaccard), not compound-target binding. The
three mirror containers exited after successful deadline pauses.
No chemical screening inputs or chemical-label evidence were observed.

Do not silently mix unrelated datasets. Require a named public or
licensed source (e.g. ChEMBL or PubChem BioAssay), permission receipt,
download/source SHA-256, assay document/target identifier,
compound/SMILES and chemical standardization method,
endpoint type (IC50/Ki/Kd/EC50/percent inhibition),
unit, censoring relation (<, >, =), dose/time, replicate/quality,
and missing-value/negative-control policy. Each independently
addressable observation gets source-content identity and occurrence
identity in FCO/FCG.

Freeze train/validation/test under scaffold and target/assay-aware
splits; check duplicate chemical and assay leakage; predefine
regression MAE/RMSE and binary AUROC/PR-AUC/calibration; preserve
unquantified or failed assay outcomes. Ablate chemical standardization,
target embeddings, assay representation, retrieval and provenance
separately. Identical split/scorer needed for causal attribution.

Tamarind Bio catalog and account authentication PASS. DiffDock,
AutoDock Vina and GNINA docking tools, ChemProp and Boltz-affinity
finetuning are offered, but accessible account lists ZERO runs,
files or trained models. No screening or affinity model was
executed. Before any paid compute, choose a valid
target/ligand file pair, validate tool schema, price estimate,
confirm terms, and obtain user/PI authorization.
