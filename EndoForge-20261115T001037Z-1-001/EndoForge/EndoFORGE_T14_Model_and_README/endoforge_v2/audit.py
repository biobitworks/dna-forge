"""Patient-bootstrap performance intervals and paired synthetic model comparisons."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def performance_intervals(predictions, repeats=200, seed=91):
    rows = []
    for (stage, variant, target), group in predictions.groupby(['stage','variant','target']):
        if group.patient_id.duplicated().any():
            raise ValueError('Bootstrap input must have one prediction per held-out patient and model.')
        rng = np.random.default_rng(seed)
        y, p = group.label.to_numpy(), group.output.to_numpy()
        values = []
        for _ in range(repeats):
            indices = rng.integers(0, len(group), len(group))
            if len(np.unique(y[indices])) == 2:
                values.append(roc_auc_score(y[indices], p[indices]))
        low, high = np.quantile(values, [.025, .975]) if values else [np.nan, np.nan]
        rows.append({'stage': stage, 'variant': variant, 'target': target, 'patients': len(group),
            'auroc': roc_auc_score(y,p) if len(np.unique(y)) == 2 else np.nan,
            'bootstrap_low': low, 'bootstrap_high': high, 'valid_resamples': len(values)})
    return pd.DataFrame(rows)


def paired_comparisons(predictions, repeats=200, seed=91):
    rows = []
    for (stage, target), group in predictions.groupby(['stage','target']):
        base = group[group.variant == 'Clinical only'].set_index('patient_id')
        full = group[group.variant == 'All available research modalities'].set_index('patient_id')
        common = base.index.intersection(full.index)
        y = base.loc[common, 'label'].to_numpy()
        if not np.array_equal(y, full.loc[common, 'label'].to_numpy()):
            raise ValueError('Paired comparison requires identical patient outcomes.')
        a, b = base.loc[common, 'output'].to_numpy(), full.loc[common, 'output'].to_numpy()
        rng = np.random.default_rng(seed)
        differences = []
        for _ in range(repeats):
            ids = rng.integers(0, len(common), len(common))
            if len(np.unique(y[ids])) == 2:
                differences.append(roc_auc_score(y[ids], b[ids])-roc_auc_score(y[ids], a[ids]))
        low, high = np.quantile(differences, [.025,.975]) if differences else [np.nan,np.nan]
        rows.append({'stage': stage, 'target': target, 'paired_patients': len(common),
            'auroc_change_full_minus_clinical': roc_auc_score(y,b)-roc_auc_score(y,a),
            'bootstrap_low': low, 'bootstrap_high': high})
    return pd.DataFrame(rows)
