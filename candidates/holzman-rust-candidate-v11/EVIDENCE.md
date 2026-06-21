# Candidate v11 Evidence

OBSOLETE HISTORICAL EVIDENCE ONLY. This file describes the old 107-task corpus and is not promotion evidence for the current 387-task generated corpus. There is no waiver path. Promotion requires a fresh full `val,test` run through `scripts/run_holzman_candidate_eval.py` with `non_promotable: false`, exact hashes, and hard `1.0` on both splits.

Candidate-only package. Live skills under `/home/lewis/.agents`, `/home/lewis/.opencode`, and `/home/lewis/.claude` were not modified.

## Exact Bundle

- Candidate: `candidates/holzman-rust-candidate-v11`
- Final evaluated skill SHA256: `6e2a6488d7dc908732d5c947f4bb5499455cb7788e5da069f3018a33423ba417`
- Bundle hashes: `reports/skillopt-training/holzman-v11-patched-full-eval/bundle_hashes.json`

## Dataset

- Dataset: `data/holzman_rust_aggressive`
- Total tasks: 107
- Split counts: train 64, val 21, test 22
- Split strategy: family-based split.

## Full Evaluation

- Full validation evidence: `reports/skillopt-training/holzman-v11-patched-full-eval/full_val`
- Full test evidence: `reports/skillopt-training/holzman-v11-patched-full-eval/full_test`
- Full summary: `reports/skillopt-training/holzman-v11-patched-full-eval/summary.json`
- Validation hard: 21/21 = `1.0`, soft `1.0`
- Test hard: 20/22 = `0.9090909090909091`, soft `0.9522727272727273`

## Targeted Rerun Of Full-Test Failures

- Targeted evidence: `reports/skillopt-training/holzman-v11-patched-targeted-final-failures`
- Targeted hard: 2/2 = `1.0`, soft `1.0`
- Passed rerun tasks: `repair_frame_sensor_mixed`, `review_invalid_state_route_typestate`

## Interpretation

- v8 was rejected because it introduced waiver/FFI language and weakened exact strict behavior.
- v9 restored absolute laws but still underperformed on explicit repair/review obligations.
- v10 recovered most behavior but still missed parse-boundary and JSON-shape details.
- Patched v11 is the strongest current candidate: it keeps absolute laws non-waivable, reaches clean full validation, and passes targeted rerun of test failures.

## Promotion Status

- Do not auto-promote.
- Full validation is clean, but full test still had two failures before targeted rerun.
- Promotion requires one fresh clean full validation/test pass on the current generated corpus and exact final hash.
