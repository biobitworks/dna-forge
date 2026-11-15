from pathlib import Path
import copy
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from endoforge_v2.simulation import (generate, snapshot, validate, STAGES, BLOCKS,
                                    TRANSCRIPTOMICS, HISTOLOGY, feature_columns)
from endoforge_v2.models import evaluate, patient_split, VARIANTS, predict, explain, available_variant
from endoforge_v2.audit import performance_intervals, paired_comparisons
from endoforge_v2.demo import representative_patient, PROFILES


@pytest.fixture(scope='module')
def cohort():
    return generate(400)


@pytest.fixture(scope='module')
def fitted(cohort):
    return evaluate(cohort)


def test_matched_ids_and_unknown_outcomes(cohort):
    validate(cohort)
    assert cohort.patients.patient_id.is_unique
    assert cohort.patients.endometriosis_label.isna().any()
    assert cohort.visits.groupby('patient_id').size().eq(8).all()


def test_reject_orphan_specimen(cohort):
    changed = copy.deepcopy(cohort)
    changed.transcriptomics.loc[0, 'patient_id'] = 'UNMATCHED'
    with pytest.raises(ValueError, match='unmatched'):
        validate(changed)


def test_no_future_information(cohort):
    before = snapshot(cohort, 0)
    changed = copy.deepcopy(cohort)
    changed.visits.loc[changed.visits.day > 0, 'pain'] = 999
    changed.transcriptomics.loc[changed.transcriptomics.sample_day > 0, TRANSCRIPTOMICS] = 999
    changed.visits.loc[changed.visits.day > 0, 'estradiol_pg_ml'] = 999
    changed.histology.loc[:, HISTOLOGY] = 999
    pd.testing.assert_frame_equal(before, snapshot(changed, 0))
    for col in ['clinical_latest_day','tx_sample_day','me_sample_day']:
        assert before[col].dropna().le(0).all()


def test_more_samples_do_not_rewrite_past(cohort):
    early, later = snapshot(cohort, 0), snapshot(cohort, 120)
    assert early.tx_sample_day.notna().sum() < later.tx_sample_day.notna().sum()
    assert set(HISTOLOGY).isdisjoint(later.columns)
    assert not any('label' in c for c in early.columns)


def test_hormonal_history_uses_observed_past(cohort):
    frame = snapshot(cohort, 0)
    patient = cohort.patients.patient_id.iloc[0]
    series = cohort.visits.query('patient_id == @patient and day <= 0').sort_values('day').estradiol_pg_ml.dropna()
    assert frame.loc[patient, 'estradiol_pg_ml_mean'] == pytest.approx(series.mean())
    assert frame.loc[patient, 'estradiol_pg_ml_change'] == pytest.approx(series.iloc[-1] - series.iloc[0])


def test_patient_split_and_unknown_exclusion(cohort, fitted):
    assert not fitted['train_ids'] & fitted['test_ids']
    assert len(fitted['train_ids'] | fitted['test_ids']) == 400
    labels = cohort.patients.set_index('patient_id')
    for _, report in fitted['reports'].iterrows():
        if report.target == 'tissue_reference_label':
            continue
        assert report.unknown_excluded == labels[report.target].isna().sum()
        assert report.n == labels.loc[sorted(fitted['test_ids']), report.target].notna().sum()
    assert set(fitted['predictions'].patient_id).issubset(fitted['test_ids'])


def test_train_only_imputation(cohort, fitted):
    stage, variant, label = next(iter(fitted['models']))
    columns = feature_columns(VARIANTS[variant])
    model = fitted['models'][(stage, variant, label)]
    frame = snapshot(cohort, STAGES[stage])
    labels = cohort.patients.set_index('patient_id')[label]
    train = frame.index.isin(fitted['train_ids']) & labels.notna().to_numpy()
    expected = frame.loc[train, columns].median().to_numpy()
    np.testing.assert_allclose(model.named_steps['simpleimputer'].statistics_, expected)


def test_explanations_and_all_missing_abstention(cohort, fitted):
    stage, variant, label = next(iter(fitted['models']))
    columns = feature_columns(VARIANTS[variant])
    model = fitted['models'][(stage, variant, label)]
    row = snapshot(cohort, 0).loc[[sorted(fitted['test_ids'])[0]], columns].astype(float)
    row.loc[:, columns[0]] = np.nan
    total = explain(model, row, columns).log_odds_contribution.sum() + model.named_steps['logisticregression'].intercept_[0]
    assert total == pytest.approx(model.decision_function(row)[0])
    row[:] = np.nan
    assert predict(model, row, columns) is None


def test_streamlit_stage_missing_modalities_and_empty_export():
    app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=90)
    assert not app.exception
    def widget(collection, label):
        return next(w for w in collection if w.label == label)
    widget(app.selectbox, 'Research information cutoff').set_value('Specialist pre-biopsy research').run(timeout=90)
    assert not app.exception
    widget(app.multiselect, 'Withhold entire modalities').set_value(VARIANTS['Clinical + hormones']).run(timeout=90)
    assert not app.exception
    assert any('output withheld' in w.value for w in app.warning)
    widget(app.multiselect, 'Synthetic label strata').set_value([]).run(timeout=90)
    assert widget(app.metric, 'Matched synthetic patients').value == '0'
    assert not app.exception


def test_available_model_falls_back_without_using_outcome(cohort):
    row = snapshot(cohort, 0).iloc[[0]].copy()
    cols = feature_columns(list(BLOCKS))
    row[cols] = row[cols].astype(float)
    row.loc[:, feature_columns(['Hormonal context','Transcriptomics','Menstrual-blood research markers'])] = np.nan
    assert available_variant(row, 'All available research modalities') == 'Clinical only'
    row.loc[:, feature_columns(['Clinical history'])] = np.nan
    assert available_variant(row, 'All available research modalities') is None


def test_patient_bootstrap_and_paired_intervals(fitted):
    intervals = performance_intervals(fitted['predictions'], repeats=20)
    assert intervals.bootstrap_low.le(intervals.bootstrap_high).all()
    paired = paired_comparisons(fitted['predictions'], repeats=20)
    assert len(paired) == 4
    assert paired.bootstrap_low.le(paired.bootstrap_high).all()
    clinical = fitted['predictions'].query("variant == 'Clinical only'").copy()
    full = clinical.copy()
    full['variant'] = 'All available research modalities'
    identical = paired_comparisons(pd.concat([clinical,full]), repeats=20)
    assert identical.auroc_change_full_minus_clinical.eq(0).all()
    assert identical.bootstrap_low.eq(0).all()


def test_demo_selection_is_label_blind(cohort, fitted):
    frame = snapshot(cohort, 0)
    for profile in PROFILES:
        chosen = representative_patient(frame, fitted['test_ids'], profile)
        assert chosen in fitted['test_ids']
        assert chosen == representative_patient(frame.copy(), fitted['test_ids'], profile)


def test_availability_routing_is_evaluated_on_test_patients(cohort, fitted):
    labels = cohort.patients.set_index('patient_id')
    for _, report in fitted['availability_reports'].iterrows():
        known = labels.loc[sorted(fitted['test_ids']),report.target].notna().sum()
        assert report.n + report.unscored_known_patients == known
