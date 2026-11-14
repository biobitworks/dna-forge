# Find the Right Patients

**DNA Forge AI x Bio Hackathon · Biobase challenge · November 14, 2026**

> Research demo on synthetic pathology reports and de-identified slides. We make no medical claims, and this is not for clinical decisions.

## In one sentence

We turned free-text pathology reports into a searchable, explainable database for finding trial-eligible patients. We used AI "fingerprints" of tissue images to identify and match slides, and connected the two, so a trial team can go from *who qualifies* to *which tissue samples we can use*.

## The problem

Clinical trials struggle to enrol enough patients. Eligible patients exist, but the facts that decide eligibility are buried in pathology reports, so someone has to read thousands of them. The challenge gave us about 10,000 computer-generated reports and 263 microscope slide images, and asked us to find the right patients and samples faster.

## What we did

### 1. Find patients in the reports
- A parser reads the final diagnosis section of each report (tumor size, lymph nodes, receptor results, and so on) and turns each report into a row in a table.
- Each of the 30 trial criteria becomes a precise filter, such as *organ = breast, HER2 = negative, positive lymph nodes ≥ 1*.
- Unlike the keyword-search baseline, the filters understand **negation** ("no invasion"), **numbers and units** (15 mm vs 25 mm) and staging codes.
- Every match records *which lines* of the report triggered it, so a person can check it in seconds.
- Where a criterion was ambiguous (does "within 3 mm" include exactly 3 mm?), we checked how the official answers treated it instead of guessing.

### 2. Understand the slide images
Each slide comes as an AI-generated numeric fingerprint of what the tissue looks like. Slides from the same organ have similar fingerprints. We used them for two jobs:
- **Which organ is this?** We trained a simple classifier on 190 labelled slides to label the 67 unknown ones.
- **Which slides look like this one?** We returned the 10 closest fingerprints, with a bonus for slides predicted to be the same organ.

**A trap we caught:** slides came from four labs, and each lab has a recognisable "house style" from its staining and scanning. A model can learn to recognise the lab instead of the organ. We removed each lab's average style before training. It costs a little accuracy on familiar labs but makes the model less fooled by lab style.

### 3. Connect the two (proof of concept)
57 slides came with their own short reports. We ran the same criteria filters on them to find slides that fit a trial, then used the "looks like this" search to suggest more slides for a pathologist to review.

### 4. Make it usable
A web app with three tabs:
- **Find patients:** pick a criterion and see how many patients qualify, with the reasons highlighted.
- **Find samples:** click a slide and see its predicted organ and its 10 most similar slides.
- **Evaluation:** our scores against the baselines, and the limitations.

## Results

| Task | Ours | Baseline |
|---|---|---|
| Patient search: mean F1 over 30 criteria | **1.00** (train) | 0.27 |
| Organ identification: accuracy | **82%** (cross-validated) | ~70% |
| Similar slides: precision at 1 / 5 / 10 | **0.85 / 0.79 / 0.74** | 0.8 / 0.7 / 0.6 |

Official scores on the hidden answer key will be added after 4:00 PM.

## Limitations
- The reports are computer-generated and very regular, which is why perfect scores were possible on train. Real reports are much messier.
- There are only a few hundred slides, so the image results are rough estimates.
- When a whole lab is held out of training, accuracy drops sharply. Lab style is still the biggest open problem.

## Run it yourself
```bash
pip install -r requirements.txt
./run_all.sh              # rebuilds every result and submission file (~3 min, CPU only)
cd app && streamlit run app.py
```
Data layout, script-by-script details and deploy steps are in [TECHNICAL.md](TECHNICAL.md). An offline version of the demo is `out/static_demo.html`.
