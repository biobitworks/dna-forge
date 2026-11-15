# Cis-male / cis-female endometriosis and PCOS: evidence gaps and governed next experiments

**Project:** biobitworks/dna-forge. **As-of:** 2026-11-14. **Status:** PROPOSED research successor, not official Biobase model or observed clinical result. [Stable citation list](REFERENCES_20261114.md) and [machine registry](CITATION_REGISTRY_20261114.json). **No human cohort, image labels, model weights, biological screening or new patient-scale outcome has been imported or trained by this plan.** **External datasets and clinical labels: NOT_ADMITTED. No new donor-level training was executed.** **Future held-out effect sizes and signed/MMR roots: NOT_COMPUTED.**

## Why a binary male/female model would be scientifically unsound

The cited studies generally report participant groups as men or women, with variably described anatomy and hormone exposure. They seldom record self-identified **cisgender** status or sex assigned at birth. Thus a reported man is not automatically verified cis male, and a woman is not automatically verified cis female. Do not assign these labels retrospectively. Endometriosis can involve people of more than one gender identity, and not all people with a uterus are women. For any new consensual dataset, **record separately, only if relevant and permitted:** self-reported gender identity, sex assigned at birth, reproductive anatomy relevant to the tissue, organ/site biopsied, age, hormone exposure and medications, menstruation or menopausal status, pregnancy history, current clinical presentation, diagnostic modality, and how each field was obtained. Use explicit MISSING / DECLINED / NOT_COLLECTED / NOT_APPLICABLE states.

The research question is not whether a sex-classifier can guess the individual. It is whether **predefined biological and clinical phenotypes** generalize across source, tissue, age, endocrine and patient groups, with rare case descriptions interpreted without exaggeration.

## Ranked gaps grounded in the citations

| ID | Research gap / affected population | Actual source evidence | What is missing / why it matters | Next measurable experiment |
|---|---|---|---|---|
| GAP01 | Rare endometrial-like tissue reports in people described as male | SRC17 is a single histologically/IHC-confirmed case | No denominator, multicenter cases, standardized exclusion of mimics, or measured cis identity; no prevalence/generalization | Pathologist-adjudicated **rare-case registry** and matched tissue differential diagnoses; report case counts, not a trained male-risk score |
| GAP02 | Population transportability for people described as female | SRC09 recruited via social media and did not collect major demographics | Spectrum/selection bias, surgical verification bias, missing hormone and condition covariates | Independent, prospective stratified clinical sample; report calibration and sensitivity at prespecified specificity |
| GAP03 | Human PCOS morphological supervision | SRC13 detects follicles in **mouse** ovarian sections; SRC14 inaccessible | No consented human PCOS histology cohort paired to clinical phenotype and appropriate controls | Secure human annotation acquisition; validate human follicle counts with pathologists; **do not diagnose PCOS from H&E alone** |
| GAP04 | Distinguishing endometriosis from histologic mimics | SRC17 and SRC18 provide selected cases/tissue stains | Scarce site-matched negative examples, gland/stroma segmentation labels, and documented differential diagnoses | Histologist-reviewed organ/site-balanced positive and hard-negative ROI set |
| GAP05 | Macrophages in menstrual effluent and lesion niche | SRC19 human study n=14 cases/19 controls; SRC20 preprint and SRC21 immune states | Menstrual day, isolation method, viable cell recovery, hormonal therapy, activation phenotype and donor pairing; no causal proof of invasive cells | Paired flow cytometry/CyTOF, morphology and scRNA/proteomics with matched donors and prespecified macrophage markers |
| GAP06 | Maternal versus fetal microchimerism | SRC15 maternal-origin hypothesis, SRC16 negative Y-FISH study in 31 patients | Y-probe cannot measure all maternal-origin cells or female fetal cells; low-frequency detection sensitivity, pregnancy history, controls and maternal genotypes often lacking | Separately preregistered cell-origin/lineage assay with maternal genotype and assay detection/false-positive validation |
| GAP07 | Truly independent endometrial transcriptomic validation | SRC10 4 case+3 controls; SRC11/SRC22 60 donors producing 466k+ cells | Small or nested effective sample size; donor/batch/menstrual-phase leakage; no linked public histology | Donor- and site-disjoint validation plus pseudobulk baseline and explicit missingness |
| GAP08 | Orthogonal proteome and tissue IHC alignment | SRC06 is a **repository**, SRC18 is an **84-tissue IHC study** highlighting MMP11/VCAN | No selected MSV accession with donor linkage, raw mass spectra, assay calibration or IHC spatial masks | Obtain source-rights-cleared MSV accession; peptide/proteoform QC; blinded pathologist IHC compartment scoring |
| GAP09 | Transferring report and WSI models into this biology | Existing Biobase A/C1/C2 are unrelated challenge outputs | No patient-to-slide join, external male/PCOS labels, or independent cross-modal validation; source domains differ | Create a NEW consented dataset with explicit tissue/donor IDs and proper train/test split; do not modify original Biobase files |
| GAP10 | Biased stratification by medication, anatomy, source or scanner | SRC09, SRC11 and Biobase supplier-shift negatives | Gender labels insufficient to capture anatomy/hormones; sources encode site/scanner shifts | Predefine hormone-status/anatomic/site subgroup tables and missingness rates; report subgroup CI and abstention |
| GAP11 | Biomarker expression versus ligandability | SRC18 MMP11/VCAN IHC, SRC04/SRC05/SRC08 Ptarmigan claims | Staining contrast is not biochemical binding, therapeutic target validity or selectivity | Independently validate target expression then separate structure-free screening from biochemical, functional and safety assays |

**Not a claim:** The rare male case does not disprove a role for retrograde menstruation in many cases, nor does the non-peer-reviewed maternal microchimerism proposal establish a universal mechanism. Y-FISH negatives do not refute all maternal-cell hypotheses. Do not use one group as a biological negative label for another.

## Model-training roadmap: gated, append-only successors

### Phase 0 — Freeze source and ethics permissions (PROPOSED, not executed)

Create an accession-based registry with per-source legal basis, permission/DUA, provenance URL, retrieval UTC, exact bytes SHA-256, participant consent scope, clinical data protection, article-versus-dataset license distinctions, de-identification and human review. Lock **record grain** (donor / biopsy / slide / ROI / cell / assay) and mappings in a private pointer table; never publish participant or slide identifiers. Disallow training on Kaggle endometriosis data until its actual license/ascertainment is verified; HistAI CC BY-NC sources are not automatically eligible for a commercial or enterprise application. GSE266265 processed 38.9 GB object requires storage/bandwidth capacity and rights verification. MassIVE requires a concrete MSV accession, not the homepage. Synthea is useful only for synthetic workflow/metadata contracts, not biological validation.

**Gate:** consent/terms PASS + sample inventory + external-holdout exclusion list + exact source identity + named PI/IRB review where required; otherwise DEFER.

### Phase 1 — Histologist annotation pilot (PROPOSED)

With site-approved slides, recruit **two independent, blinded histology readers** per stratified pilot and a third adjudicator for disagreements. Predefine labels before looking at model predictions: tissue/organ/site, glands, stroma, hemorrhage/hemosiderin, immune infiltrates (descriptive only), fibrosis, vascular structures, tissue quality, lesion subtype, uncertain/not-diagnostic and differential diagnoses. For human ovarian samples, annotate follicle stage/quality as an independent morphological task, **not PCOS** unless clinician-confirmed phenotype is separately available. On appropriate IHC panels score CD10/CK7/ER/PR (gland/stroma characterization), MMP11 and VCAN compartment/location, and explicitly sourced immune markers such as CD68/CD163 with caveats (one marker is not a unique macrophage activation phenotype). Record scanner, stain, magnification, batch, ROI pixel coordinates, reader uncertainty and the reason for ABSTAIN.

**Gate:** fixed annotation codebook; inter-reader agreement (e.g. per-class Cohen kappa and ROI IoU); adjudication log, QC controls, non-expert blind review for workflow usability, source-to-mask FCO links. Do not manufacture annotations from paper figures.

### Phase 2 — Modality-specific baselines (PROPOSED)

- **H&E morphology:** start with the Biobase-style **frozen pretrained image embedding + small linear SVM** baseline, then gland/stroma localization or a human-trained detector if enough **human** spatial masks exist. Murine SRC13 labels are external transfer-learning research, not an eligible human PCOS training set.
- **Symptoms:** fit tabular regularized logistic regression and a calibrated tree baseline on consented case/control data; model symptom missingness explicitly, compare a demographic-free baseline to allowed covariate-aware models.
- **Molecular:** use SRC10 as a small exploratory transcriptomic analysis, SRC11/SRC22 as **donor-grouped** single-cell/pseudobulk exploratory evidence, and a selected licensed MassIVE experiment for proteomics; keep modalities separate unless matched donors exist.
- **Rare male cases:** create a curated retrieval/differential-diagnosis atlas with pathology adjudication and review timing; do **not** train or report a reliable male endometriosis predictor on a handful of anecdotes.

**Gate:** predetermined, patient-grouped train/dev/locked test; source/batch disjoint and pathology-reviewed ground truth. No outcome-dependent post-hoc feature selection on locked test.

### Phase 3 — Controlled comparisons / LOMO (PROPOSED)

Define independently addressable modules: M0 hand-coded report rules, M1 frozen pathology embeddings, M2 tissue and gland/stroma segmentation, M3 donor-level symptom/clinical fields, M4 IHC/molecular readouts, M5 immune-cell state and cycle phase, M6 FCO/FCG provenance and abstention. Compare each accepted module and **full-minus-one** against the SAME frozen participants/test labels, with identical metrics/thresholds. Treat an FCO/FCG custody contribution as improved traceability unless controlled causal model performance is actually observed. Patient-cluster bootstrap CIs, externally held-out site metrics, recall/precision or mAP/IoU for objects, AUROC/AUPRC and calibration for risk/classification, and abstention/unsupported-assertion rates. Stratify reported results by the *actual recorded* identity/anatomic/hormonal variables; use UNKNOWN not imputation from anatomy.

**Gate:** reproducible Jupyter notebooks on authorized local hardware, exact environment/code/seed hashes, negative/failed attempts and calibrated uncertainty; promotion requires independent baseline comparison and reviewer approval.

### Phase 4 — Histologists, translational and drug-screening downstream (PROPOSED)

Build histologist-in-the-loop triage and error taxonomy first. Only after tissue-compartment markers and target provenance are independently validated, prioritize candidates such as **MMP11** and **VCAN** for separate **diagnostic imaging** versus **pharmacologic ligandability** questions. Ptarmigan-1 (SRC04/05/08) describes structure-free prediction; its model performance is a vendor/preprint claim. Validate any proposed small molecule with orthogonal binding assay, selectivity/off-target controls, functional readout and toxicology rather than treating docking or rank as efficacy. No such assays or Ptarmigan screens were executed in this project. The completed Tamarind ethanol descriptor smoke and local ChEMBL 25→24 normalization are **not** drug-screening training.

**Gate:** independent experimental design and consent, separate target/chemical source rights, blinded controls and clear research-only claims. Do not transfer the Biobase competition scoring to endometriosis/PCOS claims.

## Addressable evidence chain and deliverables

For every planned sample, preserve distinct atom identities and relations:

**Source accession/publication (SRCxx) → permission record → raw content hash → donor/specimen occurrence FCO → histologist annotation or instrument-readout FCO → declared typed FCG relationship → split and model execution receipt → numeric result / NEGATIVE / NULL / FAILED → bounded claim → report/figure/deck.**

The current citation list is **REFERENCES ONLY**. No experimental leaves, cryptographic root, signed attestation or MMR commitment is computed by this plan. The preexisting Biobase model source and frozen submission receipts remain immutable. Any accepted clinical dataset or model run becomes a separate successor state, with explicit responsible histologist and PI signoff.

## Near-term owner assignments and acceptance artifacts

| Owner | Next concrete artifact | Acceptance evidence |
|---|---|---|
| PI/data steward | License/consent/IRB gate matrix for GEO, Kaggle, HistAI and requested slides | Dated source-specific permission record |
| Pathologist/histologist lead | H&E/IHC ROI codebook, small blinded annotation batch and disagreement guide | Two blinded labels + adjudication + QC receipt |
| Bioinformatician | Donor-aware GSE153739 / GSE266265 intake feasibility, exact split design | Raw/processed hashes, donor counts, negative/NULL states; no uncontrolled cross-GEO join |
| Model lead (MagicPro/Studio) | Notebook and data loader using local licensed pilot, frozen SVM baseline and LOMO plan | Full reproducible run; source-to-artifact hashes; observed paired metrics |
| Reproductive-health advisor | Male-case differential, female-cohort diagnostic criteria, hormone/anatomic covariates | Signed-off schema and stratified inclusion/exclusion protocol |
| Proteomics lead | Named MassIVE accession and assay-specific metadata | MSV ID, license, samples, controls and QC |
| Chemical biology lead | Optional targeted screen after tissue-validation gate | Prespecified target/assay, cost, and orthogonal experimental plan |
| PM | Append-only PRs, presentation with actual executed/negative evidence | Reviewed artifacts; no unsupported official claims |

**NEXT_ACTION:** secure a small, rights-cleared human tissue/clinical pilot with histologist ground truth. An additional training model without such labels would generate more scores without addressing the actual sex-specific scientific gap.
