"""Leakage-aware synthetic baselines; no clinical thresholds or patient advice."""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, confusion_matrix
from .simulation import STAGES, BLOCKS, HISTOLOGY, snapshot, feature_columns, validate

VARIANTS = {
    'Clinical only': ['Clinical history'],
    'Clinical + hormones': ['Clinical history', 'Hormonal context'],
    'Clinical + transcriptomics': ['Clinical history', 'Hormonal context', 'Transcriptomics'],
    'Clinical + menstrual markers': ['Clinical history', 'Hormonal context', 'Menstrual-blood research markers'],
    'All available research modalities': list(BLOCKS),
}
LABELS = ['endometriosis_label', 'pcos_label']


def patient_split(ids, seed=29):
    shuffled = np.random.default_rng(seed).permutation(sorted(ids))
    count = int(np.ceil(len(shuffled)*.25))
    return set(shuffled[count:]), set(shuffled[:count])


def pipeline():
    return make_pipeline(SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True),
                         StandardScaler(), LogisticRegression(max_iter=1500, random_state=29))


def metrics(y, probabilities):
    y, probabilities = np.asarray(y), np.asarray(probabilities)
    tn, fp, fn, tp = confusion_matrix(y, probabilities >= .5, labels=[0,1]).ravel()
    return {'n': len(y), 'prevalence': float(y.mean()),
        'auroc': float(roc_auc_score(y, probabilities)) if len(np.unique(y)) == 2 else None,
        'average_precision': float(average_precision_score(y, probabilities)) if y.sum() else None,
        'brier': float(brier_score_loss(y, probabilities)),
        'sensitivity': float(tp/(tp+fn)) if tp+fn else None,
        'specificity': float(tn/(tn+fp)) if tn+fp else None,
        'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)}


def evaluate(cohort):
    validate(cohort)
    patients = cohort.patients.set_index('patient_id')
    train_ids, test_ids = patient_split(patients.index)
    models, reports, predictions = {}, [], []
    for stage, cutoff in STAGES.items():
        X = snapshot(cohort, cutoff)
        for variant, blocks in VARIANTS.items():
            features = feature_columns(blocks)
            for label in LABELS:
                known = patients[label].notna()
                train = X.index.isin(train_ids) & known.to_numpy()
                test = X.index.isin(test_ids) & known.to_numpy()
                model = pipeline().fit(X.loc[train, features], patients.loc[train, label])
                prob = model.predict_proba(X.loc[test, features])[:, 1]
                models[(stage, variant, label)] = model
                report = {'stage': stage, 'variant': variant, 'target': label,
                          'train_n': int(train.sum()), 'unknown_excluded': int((~known).sum()),
                          **metrics(patients.loc[test, label], prob)}
                reports.append(report)
                pred = pd.DataFrame({'patient_id': X.index[test], 'stage': stage, 'variant': variant,
                                     'target': label, 'label': patients.loc[test, label].to_numpy(), 'output': prob})
                predictions.append(pred)
    # Tissue task has its own target and specimen-selected population, not an early-diagnosis endpoint.
    tissue = cohort.histology.set_index('patient_id')
    train = tissue.index.isin(train_ids)
    test = tissue.index.isin(test_ids)
    tissue_model = pipeline().fit(tissue.loc[train, HISTOLOGY], tissue.loc[train, 'tissue_reference_label'])
    reports.append({'stage': 'Post-sampling tissue research', 'variant': 'Numeric tissue surrogates only',
        'target': 'tissue_reference_label', 'train_n': int(train.sum()), 'unknown_excluded': 0,
        **metrics(tissue.loc[test, 'tissue_reference_label'], tissue_model.predict_proba(tissue.loc[test, HISTOLOGY])[:,1])})
    result = {'models': models, 'reports': pd.DataFrame(reports), 'predictions': pd.concat(predictions, ignore_index=True),
            'train_ids': train_ids, 'test_ids': test_ids, 'tissue_model': tissue_model}
    result['availability_reports'] = availability_audit(cohort, result)
    return result


def predict(model, row, features):
    if row[features].notna().sum(axis=1).iloc[0] == 0:
        return None
    return float(model.predict_proba(row[features])[:, 1][0])


def available_variant(row, requested):
    """Use a dedicated smaller baseline when an entire requested block is absent.

    This is an engineering availability rule, not a clinical adequacy threshold.
    No output is selected on the basis of its magnitude or held-out accuracy.
    """
    allowed = set(VARIANTS[requested])
    observed = {name for name in allowed if row[BLOCKS[name]].notna().any(axis=1).iloc[0]}
    candidates = [name for name, blocks in VARIANTS.items() if set(blocks) <= observed]
    return max(candidates, key=lambda name: len(feature_columns(VARIANTS[name]))) if candidates else None


def availability_audit(cohort, fitted):
    """Evaluate the same automatic routing used in the app on held-out donors."""
    reports = []
    patients = cohort.patients.set_index('patient_id')
    for stage, cutoff in STAGES.items():
        X = snapshot(cohort, cutoff).loc[sorted(fitted['test_ids'])]
        routes = pd.Series(None, index=X.index, dtype=object)
        for variant in sorted(VARIANTS, key=lambda name: len(feature_columns(VARIANTS[name]))):
            usable = pd.Series(True, index=X.index)
            for block in VARIANTS[variant]:
                usable &= X[BLOCKS[block]].notna().any(axis=1)
            routes.loc[usable] = variant
        for label in LABELS:
            outputs = pd.Series(np.nan, index=X.index)
            for route in routes.dropna().unique():
                mask = routes.eq(route)
                features = feature_columns(VARIANTS[route])
                outputs.loc[mask] = fitted['models'][(stage, route, label)].predict_proba(X.loc[mask,features])[:,1]
            known = patients.loc[X.index,label].notna()
            scored = known & outputs.notna()
            reports.append({'stage': stage, 'target': label, 'variant': 'Availability-aware routing',
                'unscored_known_patients': int((known & ~scored).sum()),
                'routing_counts': ', '.join(f'{name}: {count}' for name,count in routes.value_counts().items()),
                **metrics(patients.loc[X.index[scored],label], outputs.loc[scored])})
    return pd.DataFrame(reports)


def explain(model, row, features):
    imputer = model.named_steps['simpleimputer']
    transformed = imputer.transform(row[features])
    scaled = model.named_steps['standardscaler'].transform(transformed)
    return pd.DataFrame({'feature': imputer.get_feature_names_out(features),
        'log_odds_contribution': scaled[0]*model.named_steps['logisticregression'].coef_[0]})
