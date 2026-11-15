"""Run from workspace root: python -m endoforge_v2.evaluate."""
from pathlib import Path
import hashlib
import json
import platform
import pandas as pd
from .simulation import generate, snapshot, STAGES
from .models import evaluate
from .audit import performance_intervals, paired_comparisons


def main():
    folder = Path(__file__).resolve().parent
    output = folder / 'outputs'
    output.mkdir(exist_ok=True)
    cohort = generate()
    result = evaluate(cohort)
    result['reports'].to_csv(output / 'metrics.csv', index=False)
    result['availability_reports'].to_csv(output / 'availability_metrics.csv', index=False)
    result['predictions'].to_csv(output / 'heldout_predictions.csv', index=False)
    performance_intervals(result['predictions']).to_csv(output / 'performance_intervals.csv', index=False)
    paired_comparisons(result['predictions']).to_csv(output / 'paired_comparisons.csv', index=False)
    for name in ['patients','visits','transcriptomics','menstrual','histology']:
        getattr(cohort, name).to_csv(output / f'synthetic_{name}.csv', index=False)
    for stage, day in STAGES.items():
        snapshot(cohort, day).to_csv(output / f'synthetic_snapshot_day_{day}.csv')
    report = {'version': 2, 'data_origin': 'synthetic_only', 'seed': 73, 'split_seed': 29,
        'prediction_sha256': hashlib.sha256(result['predictions'].to_csv(index=False).encode('utf-8')).hexdigest(),
        'python': platform.python_version(), 'train_patients': len(result['train_ids']),
        'test_patients': len(result['test_ids']),
        'patient_overlap': len(result['train_ids'] & result['test_ids']),
        'source_sha256': {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                          for name in ['simulation.py','models.py','evaluate.py','audit.py','demo.py']},
        'rows': {name: len(getattr(cohort, name)) for name in ['patients','visits','transcriptomics','menstrual','histology']},
        'limitations': ['Invented generator, labels and assay features; no clinical validation.',
                       'Same synthetic population at both care stages; no real referral decision target.',
                       'Numeric tissue surrogates only; no histology images.',
                       'No clinical uncertainty intervals or external-site validation.']}
    (output / 'run_record.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print(result['reports'][['stage','variant','target','n','auroc','sensitivity','specificity']].to_string(index=False))


if __name__ == '__main__':
    main()
