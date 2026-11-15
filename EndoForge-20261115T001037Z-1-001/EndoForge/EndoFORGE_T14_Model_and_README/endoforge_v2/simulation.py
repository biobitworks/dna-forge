"""Invented matched patients and time-stamped assays. Not physiological validation."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

CLINICAL = ['age', 'family_history', 'symptom_months', 'cycle_days', 'pain_mean',
            'pain_max', 'bowel_pain_mean', 'pelvic_pain_mean', 'impact_mean',
            'bleeding_mean', 'androgen_signs_mean']
HORMONES = ['estradiol_pg_ml', 'progesterone_ng_ml', 'lh_iu_l', 'fsh_iu_l',
            'testosterone_ng_dl', 'phase_sin', 'phase_cos', 'hormonal_treatment']
HORMONE_HISTORY = [f'{name}_{summary}' for name in ['estradiol_pg_ml','progesterone_ng_ml','testosterone_ng_dl']
                   for summary in ['mean','std','change']] + ['treatment_fraction', 'hormone_observations']
TRANSCRIPTOMICS = [f'tx_feature_{i:02d}_au' for i in range(1, 13)]
MENSTRUAL = ['me_inflammation_au', 'me_stromal_response_au',
             'me_immune_balance_au', 'me_sample_quality_au']
HISTOLOGY = ['tissue_gland_stroma_au', 'tissue_fibrosis_au', 'tissue_immune_au']
BLOCKS = {'Clinical history': CLINICAL, 'Hormonal context': HORMONES + HORMONE_HISTORY,
          'Transcriptomics': TRANSCRIPTOMICS, 'Menstrual-blood research markers': MENSTRUAL}
STAGES = {'Primary-care research': 0, 'Specialist pre-biopsy research': 120}


@dataclass
class Cohort:
    patients: pd.DataFrame
    visits: pd.DataFrame
    transcriptomics: pd.DataFrame
    menstrual: pd.DataFrame
    histology: pd.DataFrame


def generate(n=1200, seed=73):
    if n < 100:
        raise ValueError('Use at least 100 synthetic patients for the demo.')
    rng = np.random.default_rng(seed)
    ids = np.array([f'V2-SYN-{i:05d}' for i in range(n)])
    endo = rng.binomial(1, .30, n)
    pcos = rng.binomial(1, .18 + .08 * endo, n)
    mimic = rng.binomial(1, .24, n)
    severity = rng.normal(0, 1, n)
    age = rng.integers(18, 46, n)
    cycle = np.clip(rng.normal(29 + 10 * pcos, 7, n), 19, 80)
    treatment = rng.binomial(1, .30, n)
    patients = pd.DataFrame({'patient_id': ids, 'age': age,
        'family_history': rng.binomial(1, .12 + .18 * endo),
        'symptom_months': rng.integers(3, 85, n), 'site': rng.choice(['A','B','C','D'], n),
        'endometriosis_label': endo.astype(float), 'pcos_label': pcos.astype(float),
        'label_available_day': 240, 'data_origin': 'synthetic_v2'})
    # Unknown outcomes remain unknown, never recoded as disease-negative.
    for label in ['endometriosis_label', 'pcos_label']:
        patients.loc[rng.random(n) < .07, label] = np.nan
    visits = []
    for day in [-150, -120, -90, -60, -30, 0, 60, 120]:
        phase = rng.uniform(0, 1, n)  # Known synthetic phase; real phase may be unknown.
        angle = 2 * np.pi * phase
        menstrual_phase = (phase < .18).astype(float)
        treated = treatment if day <= 0 else np.maximum(treatment, rng.binomial(1, .12, n))
        pain = np.clip(2 + 2.4*endo + 1.5*mimic + severity +
                       1.2*menstrual_phase - 1.1*treated + rng.normal(0, 1.7, n), 0, 10)
        visit = pd.DataFrame({'patient_id': ids, 'day': day, 'cycle_days': cycle,
            'pain': pain,
            'bowel_pain': rng.binomial(1, np.clip(.10 + .38*endo + .18*mimic, 0, 1)),
            'pelvic_pain': rng.binomial(1, .16 + .40*endo + .12*mimic),
            'impact': np.clip(pain*.7 + rng.normal(0, 1.5, n), 0, 10),
            'bleeding': np.clip(3 + .5*endo + mimic + rng.normal(0, 2, n), 0, 10),
            'androgen_signs': rng.binomial(1, .12 + .48*pcos),
            'estradiol_pg_ml': np.clip((100 + 65*np.sin(angle-.7)) * (1-.4*treated) + rng.normal(0, 25, n), 5, 350),
            'progesterone_ng_ml': np.clip((.7 + 9*np.maximum(0, -np.sin(angle))) * (1-.7*treated) + rng.normal(0, 1.2, n), .1, 25),
            'lh_iu_l': np.clip(5 + 3*pcos + 8*np.exp(-((phase-.5)/.08)**2) + rng.normal(0, 3, n), .1, 40),
            'fsh_iu_l': np.clip(6 + rng.normal(0, 2, n), .1, 20),
            'testosterone_ng_dl': np.clip(28 + 25*pcos + rng.normal(0, 16, n), 2, 130),
            'phase_sin': np.sin(angle), 'phase_cos': np.cos(angle),
            'hormonal_treatment': treated.astype(float)})
        for col in visit.columns.difference(['patient_id', 'day']):
            visit.loc[rng.random(n) < (.15 if col in HORMONES else .06), col] = np.nan
        visits.append(visit)

    def sample_table(columns, probability):
        table = pd.DataFrame({'patient_id': ids,
            'sample_day': rng.choice([-10, 45, 100, 160], n),
            'sample_cycle_phase': rng.uniform(0, 1, n),
            'treatment_at_collection': treatment})
        phase_effect = np.sin(2*np.pi*table.sample_cycle_phase.to_numpy())
        shared = rng.normal(0, 1, n)
        for i, name in enumerate(columns):
            # Abstract assay values: not real genes, concentrations, or validated markers.
            table[name] = (.5*endo if i % 3 == 0 else .3*pcos) + .35*shared + \
                .6*phase_effect - .25*treatment + rng.normal(0, 1, n)
            table.loc[rng.random(n) < .10, name] = np.nan
        return table.loc[rng.random(n) < probability].reset_index(drop=True)

    tx = sample_table(TRANSCRIPTOMICS, .76)
    menstrual = sample_table(MENSTRUAL, .80)
    histology = pd.DataFrame({'patient_id': ids, 'sample_day': 180,
        'tissue_reference_label': (rng.random(n) < (.12 + .68*endo)).astype(int)})
    for feature in HISTOLOGY:
        histology[feature] = histology.tissue_reference_label*.9 + rng.normal(0, 1, n)
    histology = histology.loc[rng.random(n) < (.25 + .30*endo)].reset_index(drop=True)
    return Cohort(patients, pd.concat(visits, ignore_index=True), tx, menstrual, histology)


def validate(cohort):
    p = cohort.patients
    if p.patient_id.isna().any() or p.patient_id.duplicated().any():
        raise ValueError('Patient IDs must be present and unique.')
    ids = set(p.patient_id)
    for name in ['visits', 'transcriptomics', 'menstrual', 'histology']:
        table = getattr(cohort, name)
        if table.patient_id.isna().any() or not set(table.patient_id).issubset(ids):
            raise ValueError(f'{name}: unmatched patient IDs.')
        key = ['patient_id', 'day'] if name == 'visits' else ['patient_id']
        if table.duplicated(key).any():
            raise ValueError(f'{name}: duplicate records require explicit aggregation.')


def snapshot(cohort, cutoff):
    """Build features strictly from information at/before the prediction day."""
    validate(cohort)
    p = cohort.patients.set_index('patient_id')
    result = p[['age','family_history','symptom_months']].copy()
    visits = cohort.visits.loc[cohort.visits.day <= cutoff].sort_values('day')
    means = visits.groupby('patient_id')[['pain','bowel_pain','pelvic_pain','impact','bleeding','androgen_signs']].mean()
    means = means.rename(columns={c: f'{c}_mean' for c in means.columns})
    result = result.join(means)
    result['pain_max'] = visits.groupby('patient_id').pain.max()
    # Latest visit, NOT groupby.last(): do not silently fill missing latest values from older visits.
    latest = visits.drop_duplicates('patient_id', keep='last').set_index('patient_id')
    result = result.join(latest[['cycle_days'] + HORMONES])
    grouped = visits.groupby('patient_id')
    for hormone in ['estradiol_pg_ml','progesterone_ng_ml','testosterone_ng_dl']:
        result[f'{hormone}_mean'] = grouped[hormone].mean()
        result[f'{hormone}_std'] = grouped[hormone].std()
        # Differences summarize observed history, not phase-adjusted biological change.
        result[f'{hormone}_change'] = grouped[hormone].last() - grouped[hormone].first()
    result['treatment_fraction'] = grouped.hormonal_treatment.mean()
    result['hormone_observations'] = grouped.estradiol_pg_ml.count().astype(float)
    result['clinical_latest_day'] = latest.day
    for name, table, columns in [('tx', cohort.transcriptomics, TRANSCRIPTOMICS),
                                  ('me', cohort.menstrual, MENSTRUAL)]:
        available = table.loc[table.sample_day <= cutoff].set_index('patient_id')
        result = result.join(available[columns])
        # Collection phase/treatment are explicitly retained for assay interpretation.
        result[f'{name}_sample_day'] = available.sample_day
        result[f'{name}_phase'] = available.sample_cycle_phase
        result[f'{name}_treatment'] = available.treatment_at_collection
    result['data_origin'] = 'synthetic_v2'
    return result


ASSAY_CONTEXT = ['tx_phase', 'tx_treatment', 'me_phase', 'me_treatment']


def feature_columns(block_names):
    columns = [c for name in block_names for c in BLOCKS[name]]
    if 'Transcriptomics' in block_names:
        columns += ['tx_phase', 'tx_treatment']
    if 'Menstrual-blood research markers' in block_names:
        columns += ['me_phase', 'me_treatment']
    return columns
