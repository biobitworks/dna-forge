## Summary

<!-- What does this PR change, and why? -->

## Linked issue

Closes #

## How it was run

- Run id: `runs/<run-id>/`
- Host:
- Commit:

## Results

Keep the two splits apart. Never mix them in one number.

| Metric | Local leave-one-out | Answer key |
| ------ | ------------------- | ---------- |
|        |                     |            |

Any number produced after 4 PM (after the answer key is out) is marked
**post-hoc** and is not used to choose the submission.

## Checklist

- [ ] No challenge data, labels or embeddings added (slides, tiles,
      thumbnails, vectors, manifests, reports). `python3 scripts/check_no_data.py` passes.
- [ ] `runs/<run-id>/record.json` is included for every number reported above,
      with the core RunRecord fields (`dnaforge/custody.py`): `kind`, `id`,
      `code`, `inputs`, `outputs`.
- [ ] Output and submission files are hashed (SHA-256 in the run record).
- [ ] WORKSTREAM.md updated if this claims or finishes a piece of work.
- [ ] If a new model is used, its licence is noted in DATA_POLICY.md.
