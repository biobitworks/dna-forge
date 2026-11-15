"""Demo navigation based on observed histories, never labels or model outputs."""
import numpy as np

PROFILES = ['Browse cohort', 'Persistent pain pattern', 'Overlapping symptom pattern', 'Hormonal treatment context']


def representative_patient(frame, patient_ids, profile):
    candidates = frame.loc[sorted(patient_ids)]
    if profile == 'Persistent pain pattern':
        match = candidates[candidates.pain_mean >= 5]
    elif profile == 'Overlapping symptom pattern':
        match = candidates[(candidates.pain_mean >= 4) & (candidates.cycle_days >= 35)]
    elif profile == 'Hormonal treatment context':
        match = candidates[candidates.hormonal_treatment == 1]
    else:
        return candidates.index[0]
    if match.empty:
        return candidates.index[0]
    # Choose the middle clinical pain profile, not the strongest model response.
    distances = (match.pain_mean - match.pain_mean.median()).abs().fillna(np.inf)
    return distances.idxmin()
