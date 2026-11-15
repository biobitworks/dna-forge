# EndoFORGE V2 — synthetic multimodal research

An independent local prototype for exploring earlier primary-care identification
and specialist pre-biopsy investigation. **Not validated for diagnosis, referral,
triage or clinical use.** Version 1 is unchanged. V2 imports no code from V1.

## Start on this computer

Double-click `run_app.bat` and open http://127.0.0.1:8503. The launcher can reuse
the already installed environment alongside V1 without modifying V1's source.
No new package installation is needed on this computer.

For a separate installation, open PowerShell in `endoforge_v2`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8503
```

On macOS/Linux, use `python3 -m venv .venv` and `.venv/bin/python`.
The server binds only to loopback and usage telemetry is disabled. No uploads,
paid APIs, remote inference, or cloud services. Dependencies need network access
only during installation. All inputs and outputs must remain synthetic.

## What V2 adds

The hackathon demo also includes guided patient journeys selected without using
outcome labels, automatic fallback to dedicated smaller models when complete
modalities are absent, a held-out evaluation of that routing, percentile
bootstrap AUROC intervals, and paired combined-versus-clinical comparisons.
The intervals resample held-out patients for already-fitted models; they do not
measure patient-level uncertainty, training uncertainty or clinical accuracy.
See `PITCH.txt` for a two-minute script and a short live-demo sequence.

1. A matched synthetic cohort with repeated visits and specimen timestamps.
2. Clinical symptoms and their histories, laboratory hormone measurements with
   cycle context, treatment exposure, abstract transcriptomic features, and
   abstract menstrual-effluent marker values.
3. Two pre-biopsy research views: day 0 and day 120. Features are constructed
   only from information available by that cutoff. Later outcome labels remain
   outside the feature matrix.
4. Separate endometriosis and PCOS logistic-regression models, plus comparisons
   of clinical-only, hormone-aware, molecular and combined feature sets.
5. Exact additive model explanations including missing-indicator contributions,
   modality withholding, missing-field controls, calibration tables and exports.
6. A separate day-180 tissue-pattern experiment using numeric surrogates only.
   This is not a histology image model and cannot improve the pre-biopsy score.

## Beginner explanation

The generator first invents patient conditions, including overlapping PCOS and
endometriosis and symptom mimics. It then invents noisy observations. Some
outcome labels and measurements are left unknown. It is deliberately possible
to have symptoms without either generated condition.

The same donor ID links every visit and sample. A patient is assigned once to
training or testing. Neither records nor tissue patches from that donor can
cross the split. Unknown outcome labels are excluded separately for each target.

At each research cutoff, the model sees only earlier information. The two views
predict the same later invented disease labels. They do NOT predict a validated
referral decision or assess urgency. The specialist population is not separately
sampled; it is the same synthetic cohort with more observations.

Training-only median imputation, missing indicators and scaling precede simple
logistic regressions. Missing inputs do not imply normal findings. All-missing
cases are withheld; partially observed cases remain experimental.

For hormones, V2 stores estradiol, progesterone, LH, FSH and testosterone with
units, phase encodings and a simplified hormonal-treatment flag. These invented
trajectories are not physiological reference ranges. The code does not assume
high estrogen diagnoses endometriosis or that treatment response proves disease.
Collection-phase and treatment metadata accompany molecular observations.
Hormonal-history features include observed means, variability and change between
the earliest and latest available measurements, plus treatment exposure fraction.
These raw changes are not phase-adjusted and have no causal interpretation.

Transcriptomic features and menstrual biomarkers have explicitly abstract names
and arbitrary units. No actual gene-expression processing or validated biomarker
assay is implemented. Hormonal medications, irregular phase estimates, cell
composition, laboratory batch and sample quality require much more realistic
modeling before real-data work.

## Generate results and run tests

From the workspace directory containing `endoforge_v2`:

```powershell
.\endoforge\.venv\Scripts\python.exe -m endoforge_v2.evaluate
.\endoforge\.venv\Scripts\python.exe -m pytest endoforge_v2\test_v2.py -q
```

The evaluation writes synthetic tables, held-out predictions, metrics and a
source-hashed run record to ignored `endoforge_v2/outputs/`. These remain local.
The tests check matching, time-cutoff leakage, patient separation, unknown-label
exclusion, train-only preprocessing, explanations, missingness and app behavior.

## Limitations and next research steps

Synthetic performance is driven by the generator's assumptions and cannot
establish diagnostic accuracy, generalizability or clinical utility. This is a
single split with no clinical uncertainty intervals or external validation.
Treatment and hormones are simplified; there are no causal conclusions.
Missingness and access to assays can create selection bias. Availability is
not a biological signal, and ablation comparisons do not establish which tests
should be ordered. Assay-rich patients need separate evaluation in real cohorts.

Adults only; no adolescent, pregnancy, postpartum or menopause modeling. No
urgent-care rules, imaging interpretation, treatment selection or diagnostic
exclusion. Clinical guidance must remain independent of experimental scores.
Histology uses numeric surrogates, not images; its specimen-selected population
cannot demonstrate earlier primary-care detection. Early care-pathway detection
is not the same as anatomically early-stage disease.

A useful future endpoint would be clinician-adjudicated need for specialist
assessment, evaluated prospectively, rather than inventing referral labels from
the model's own symptoms. A matched real-data study must keep each donor's
samples together, define prediction time and independent outcomes, assess
calibration and subgroup performance, and validate externally.

## Evidence informing the design

- [NICE NG73](https://www.nice.org.uk/guidance/ng73/chapter/Recommendations):
  ultrasound in suspected disease; normal imaging does not exclude endometriosis;
  serum CA125 should not be used for diagnosis. Imaging input remains future work.
- [GEO GSE203191](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE203191):
  menstrual-effluent single-cell research with confirmed cases, controls and
  symptomatic undiagnosed participants. The latter are not verified negatives.
- [Cycle-bias research](https://pmc.ncbi.nlm.nih.gov/articles/PMC8063681/):
  menstrual timing can confound endometrial biomarker studies.

No data were downloaded from these sources. Real reuse requires metadata,
consent/permission, sample-to-donor and label-standard audits. Public molecular
data do not establish a matched clinical, hormonal and histology cohort.
