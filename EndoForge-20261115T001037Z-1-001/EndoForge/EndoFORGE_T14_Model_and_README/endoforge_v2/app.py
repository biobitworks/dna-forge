"""Local V2 research dashboard. No clinical use; no uploads or remote services."""
from pathlib import Path
import sys
import hashlib
import json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd
import streamlit as st
from endoforge_v2.simulation import (generate, snapshot, STAGES, BLOCKS, HORMONES,
                                    HISTOLOGY, feature_columns)
from endoforge_v2.models import evaluate, VARIANTS, LABELS, predict, explain, available_variant
from endoforge_v2.audit import performance_intervals, paired_comparisons
from endoforge_v2.demo import PROFILES, representative_patient

st.set_page_config(page_title='EndoFORGE V2 | Synthetic research', page_icon='🧬', layout='wide')
st.markdown('''<style>
.block-container {max-width:1250px;padding-top:2rem;}
[data-testid="stMetric"] {background:rgba(20,160,150,.09);border-radius:12px;padding:14px;}
</style>''', unsafe_allow_html=True)
st.title('EndoFORGE AI')
st.subheader('Connect the history. Contextualize the hormones. Trace the evidence.')
st.warning('SYNTHETIC RESEARCH DEMO. Not validated for diagnosis, referral, triage, treatment, or patient care. '
           'Use synthetic inputs only. Outputs are simulated model behavior, not disease risk.')
st.caption('Independent Version 2. Clinical history → optional molecular evidence → separate post-sampling tissue research. '
           'Hormonal timing and treatment context accompany the measurements. No clinical action is automated.')


@st.cache_resource
def load():
    cohort = generate()
    return cohort, evaluate(cohort)


cohort, fitted = load()


@st.cache_data
def audit_tables(predictions):
    folder = Path(__file__).resolve().parent
    output = folder / 'outputs'
    manifest = output / 'run_record.json'
    if manifest.exists():
        record = json.loads(manifest.read_text(encoding='utf-8'))
        current_predictions = hashlib.sha256(predictions.to_csv(index=False).encode('utf-8')).hexdigest()
        sources_match = all(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
                            for name,digest in record.get('source_sha256', {}).items())
        tables_exist = all((output / name).exists() for name in ['performance_intervals.csv','paired_comparisons.csv'])
        if sources_match and tables_exist and record.get('prediction_sha256') == current_predictions:
            return pd.read_csv(output / 'performance_intervals.csv'), pd.read_csv(output / 'paired_comparisons.csv')
    return performance_intervals(predictions), paired_comparisons(predictions)


intervals, paired = audit_tables(fitted['predictions'])
overview, case, comparison, browser, tissue, methods = st.tabs([
    'Pitch overview', 'Patient journey', 'Model evidence', 'Research cohorts', 'Tissue research', 'Evidence and limitations'])

with overview:
    st.subheader('One patient timeline. Multiple evidence layers. Every output explained.')
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown('**The challenge**\n\nSymptoms, hormone measurements and research assays arrive at different times. A single snapshot loses that context.')
    with col2:
        st.markdown('**The working prototype**\n\nA local evidence workspace joins matched histories and assays, preserves unknowns, and explains separate endometriosis and PCOS outputs.')
    with col3:
        st.markdown('**The next milestone**\n\nEvaluate with clinician-adjudicated outcomes and independent prospective cohorts. Earlier identification remains a research objective.')
    st.markdown('**Live demo:** choose a patient journey → compare care-stage cutoffs → withhold an assay → inspect the explanation → export a matched research cohort.')
    st.subheader('Two questions, with different information cutoffs')
    st.dataframe(pd.DataFrame([
        {'View': 'Primary-care research', 'Cutoff': 'Day 0', 'Target': 'Later synthetic endometriosis / PCOS label',
         'Inputs': 'History and hormones; molecular samples only if already available'},
        {'View': 'Specialist pre-biopsy research', 'Cutoff': 'Day 120', 'Target': 'Later synthetic endometriosis / PCOS label',
         'Inputs': 'Updated history and any matched molecular samples collected by day 120'},
        {'View': 'Tissue research', 'Cutoff': 'Day 180', 'Target': 'Separate simulated tissue reference label',
         'Inputs': 'Numeric tissue surrogates; no real slides or image model'}]), hide_index=True)
    a,b,c,d = st.columns(4)
    a.metric('Synthetic research cohort', len(cohort.patients))
    b.metric('Training patients', len(fitted['train_ids']))
    c.metric('Held-out patients', len(fitted['test_ids']))
    d.metric('Patient overlap', len(fitted['train_ids'] & fitted['test_ids']))
    st.info('The target is an invented later disease label, not an independently validated referral decision. '
            'The specialist view uses the same simulated population, not a representative specialist cohort. '
            'Earlier identification in a care pathway is not the same as detecting anatomically early-stage disease.')

with case:
    stage = st.selectbox('Research information cutoff', list(STAGES))
    variant = st.selectbox('Experimental model inputs', list(VARIANTS), index=1)
    cutoff = STAGES[stage]
    frame = snapshot(cohort, cutoff)
    profile = st.selectbox('Demo journey', PROFILES)
    candidates = sorted(fitted['test_ids'])
    selected = representative_patient(frame, fitted['test_ids'], profile)
    patient_id = st.selectbox('Held-out synthetic patient', candidates, index=candidates.index(selected), key=f'patient_{stage}_{profile}')
    st.caption('Demo journeys are selected from observed clinical histories, never from disease labels or favorable model outputs.')
    row = frame.loc[[patient_id]].copy()
    numeric = feature_columns(list(BLOCKS))
    row[numeric] = row[numeric].astype(float)
    features = feature_columns(VARIANTS[variant])
    visits = cohort.visits.query('patient_id == @patient_id and day <= @cutoff').sort_values('day')
    st.subheader('Stored synthetic history')
    st.line_chart(visits.set_index('day')[['pain','impact']])
    st.caption('Days are relative to the simulated first visit. This timeline shows stored history; scenario edits below change derived case inputs only.')
    with st.expander('Hormone measurements, timing and treatment'):
        st.dataframe(visits[['day'] + HORMONES], hide_index=True)
        st.dataframe(row[[c for c in BLOCKS['Hormonal context'] if c not in HORMONES]])
        st.caption('Units: estradiol pg/mL; progesterone ng/mL; LH/FSH IU/L; testosterone ng/dL. '
                   'Phase sine/cosine encode invented cycle phase. Treatment is a simplified binary context flag. '
                   'These distributions are illustrative and are not physiological reference ranges. '
                   'History summaries include means, variability and latest-minus-earliest observed change. '
                   'Raw changes are not phase-adjusted and are not interpreted as causal or diagnostic evidence.')
    with st.expander('Edit synthetic scenario inputs'):
        edit = st.checkbox('Enable scenario edits', value=False)
        if edit:
            for feature in ['age','cycle_days','pain_mean','impact_mean'] + [f for f in HORMONES[:5] if f in features]:
                value = row.iloc[0][feature]
                current = float(value) if pd.notna(value) else 0.0
                row.loc[:,feature] = st.number_input(feature, min_value=0.0, value=current, key=f'edit_{patient_id}_{stage}_{feature}')
            st.caption('Replacing a missing measurement here explicitly supplies a synthetic value; preserve it as unknown using the missing-field selector.')
    omitted = st.multiselect('Withhold entire modalities', VARIANTS[variant])
    for block in omitted:
        row.loc[:, feature_columns([block])] = np.nan
    missing = st.multiselect('Additional fields to mark unknown', features)
    row.loc[:, missing] = np.nan
    automatic = st.checkbox('Use an availability-aware baseline', value=True)
    active = available_variant(row, variant) if automatic else variant
    if active is not None:
        features = feature_columns(VARIANTS[active])
        st.info(f'Active baseline: {active}. Entirely absent modalities are handled by a dedicated smaller model when possible. '
                'Availability does not establish clinical adequacy.')
    else:
        st.warning('No supported clinical baseline has observed inputs. Outputs are withheld.')
    observed = int(row[features].notna().sum(axis=1).iloc[0])
    st.write(f'Observed fields: {observed}/{len(features)}. Missing fields: {len(features)-observed}.')
    st.dataframe(pd.DataFrame([{'modality': name,
        'observed_features': int(row[BLOCKS[name]].notna().sum(axis=1).iloc[0]),
        'total_features': len(BLOCKS[name])} for name in VARIANTS[variant]]), hide_index=True)
    st.caption(f"Transcriptomic sample day: {row.iloc[0]['tx_sample_day']}; menstrual sample day: {row.iloc[0]['me_sample_day']}. "
               'NaN means no eligible sample at this cutoff. Withholding a modality hides its values from the model.')
    values = {}
    for label in LABELS:
        model = fitted['models'][(stage, active, label)] if active is not None else None
        output = predict(model, row, features) if model is not None else None
        values[label] = output
        if output is None:
            st.warning(f'{label}: no observed inputs; output withheld.')
            continue
        st.metric(f'{label.replace("_label", "").title()} — synthetic model score', f'{output:.3f}')
        terms = explain(model, row, features)
        with st.expander(f'Contributions: {label}'):
            ranked = terms.reindex(terms.log_odds_contribution.abs().sort_values(ascending=False).index).head(10)
            st.bar_chart(ranked.set_index('feature').log_odds_contribution)
            st.dataframe(terms, hide_index=True)
            st.caption('Exact log-odds contributions relative to training means; missing-indicator terms are included. '
                       'Terms plus the intercept reconstruct the fitted model calculation. They are associations, not causal explanations.')
    if all(v is not None for v in values.values()):
        elevated = [name.replace('_label','') for name,val in values.items() if val >= .5]
        st.info('Synthetic display pattern: ' + (' + '.join(elevated) if elevated else 'neither output at or above 0.50') +
                '. This is not a diagnosis, exclusion, or referral recommendation.')
    st.warning('Uncertainty is not clinically quantified. Missing modalities use training-only imputation and missing indicators. '
               'More available measurements do not guarantee a more accurate result. Scores near 0.50 are only ambiguous under an arbitrary display convention.')
    st.download_button('Export synthetic scenario inputs', row.to_csv(index=True).encode('utf-8'),
                       file_name='synthetic_v2_scenario.csv', mime='text/csv')

with comparison:
    st.subheader('Availability-aware model evaluation')
    st.dataframe(fitted['availability_reports'], hide_index=True)
    st.caption('Evaluated routing uses observed modality availability only. It selects a dedicated trained baseline without choosing the highest score. '
               'Partial-field imputation can still occur within an available modality.')
    st.subheader('Does adding modalities help? Measure it instead of assuming it.')
    st.dataframe(paired, hide_index=True)
    st.caption('Paired comparison: combined minus clinical-only AUROC on the same held-out patients. '
               'Intervals are percentile bootstrap intervals from 200 patient resamples of a fixed test set. '
               'They do not include training uncertainty, generator uncertainty, or clinical generalization.')
    st.subheader('Synthetic performance intervals')
    st.dataframe(intervals, hide_index=True)
    st.download_button('Export synthetic evidence table', intervals.to_csv(index=False).encode('utf-8'),
                       file_name='synthetic_v2_evidence.csv', mime='text/csv')
    st.subheader('Held-out synthetic model behavior')
    st.dataframe(fitted['reports'], hide_index=True)
    st.caption('Threshold 0.50 is a display convention. Average precision should be compared with prevalence. '
               'Brier score measures probability error; it does not establish clinical calibration. Unknown labels are excluded separately per target.')
    view = st.selectbox('Calibration view', list(STAGES), key='calibration_stage')
    target = st.selectbox('Calibration target', LABELS)
    pred = fitted['predictions']
    pred = pred[(pred.stage == view) & (pred.target == target) & (pred.variant == 'All available research modalities')].copy()
    pred['bin'] = pd.cut(pred.output, bins=np.linspace(0,1,6), include_lowest=True)
    bins = pred.groupby('bin', observed=True).agg(mean_output=('output','mean'),
        observed_fraction=('label','mean'), patients=('label','size')).reset_index()
    bins['bin'] = bins.bin.astype(str)
    st.dataframe(bins, hide_index=True)
    st.caption('This calibration table describes only the synthetic held-out population. There is no external validation or patient-level clinical uncertainty estimate.')

with browser:
    st.subheader('Matched synthetic research cohort')
    export_stage = st.selectbox('Cohort information cutoff', list(STAGES), key='cohort_stage')
    data = snapshot(cohort, STAGES[export_stage]).join(cohort.patients.set_index('patient_id')[LABELS + ['site']])
    data['stratum'] = np.select([data[LABELS].isna().any(axis=1),
        (data.endometriosis_label == 1) & (data.pcos_label == 1), data.endometriosis_label == 1,
        data.pcos_label == 1], ['Unknown outcome','Overlap','Endometriosis labeled','PCOS labeled'], default='Neither labeled')
    groups = st.multiselect('Synthetic label strata', sorted(data.stratum.unique()), default=sorted(data.stratum.unique()))
    require = st.multiselect('Require matched assays available at cutoff', ['Transcriptomics','Menstrual-blood research markers'])
    filtered = data[data.stratum.isin(groups)]
    for block in require:
        filtered = filtered.loc[filtered[BLOCKS[block]].notna().any(axis=1)]
    st.metric('Matched synthetic patients', len(filtered))
    st.dataframe(filtered.head(100))
    st.caption('Preview: first 100 rows. Export: every matched row, including explicitly synthetic outcome labels. '
               'Labels are for research evaluation; they are never model features. Neither-labeled is not a verified healthy control.')
    st.download_button('Export synthetic cohort', filtered.to_csv(index=True).encode('utf-8'),
                       file_name='synthetic_v2_cohort.csv', mime='text/csv')

with tissue:
    st.subheader('Separate post-sampling tissue experiment')
    st.info('This is a numeric-surrogate demonstration, not a histology image model or pathology interpretation. '
            'Tissue sampled at day 180 cannot enter either pre-biopsy model. No biopsy is suggested by the app.')
    available = cohort.histology[cohort.histology.patient_id.isin(fitted['test_ids'])].set_index('patient_id')
    specimen = st.selectbox('Held-out synthetic tissue specimen', list(available.index))
    output = predict(fitted['tissue_model'], available.loc[[specimen]], HISTOLOGY)
    st.metric('Synthetic tissue-pattern output', f'{output:.3f}')
    st.dataframe(available.loc[[specimen], HISTOLOGY])
    st.caption('Separate target: invented tissue_reference_label. Specimen selection depends on generated disease status, '
               'so this subset is biased and cannot represent early primary-care performance.')

with methods:
    st.markdown('''### Research boundaries
- Primary-care and specialist views share the same patient split. All visits and samples stay with their donor.
- Features are constructed before each cutoff; day-240 reference labels are outcomes only.
- Unknown labels are excluded, not treated as negatives. Missing predictors are preserved until training-only imputation.
- Molecular and menstrual features are arbitrary simulated assay variables, not real genes, commercial tests, or validated biomarkers.
- Hormones are contextual measurements, not an endometriosis diagnostic panel. Cycle and treatment effects can confound molecular signals.
- Histology uses numeric surrogates only. Ultrasound/MRI interpretation, real transcriptomics processing and whole-slide image analysis remain future work.
- Scores cannot diagnose, exclude disease, select treatment or establish referral urgency. No clinical thresholds are implemented.
- No external validation, representative population sampling, clinical uncertainty intervals, or demonstrated improvement in diagnosis time.

### Evidence informing the design
NICE recommends ultrasound for suspected endometriosis, cautions that normal imaging does not exclude it, and advises against CA125 as a diagnostic test.
[NICE NG73](https://www.nice.org.uk/guidance/ng73/chapter/Recommendations)

Menstrual-effluent single-cell study GSE203191 includes confirmed cases, controls and symptomatic but undiagnosed participants. That last group must not be silently labeled negative.
[GEO GSE203191](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE203191)

Cycle-related confounding requires explicit assessment in endometrial biomarker studies.
[Primary research](https://pmc.ncbi.nlm.nih.gov/articles/PMC8063681/)

These sources inform the research design. No real patient data were downloaded or used in this demo.''')
