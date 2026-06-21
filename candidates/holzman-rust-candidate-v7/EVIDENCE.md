# Candidate v7 Evidence

OBSOLETE HISTORICAL EVIDENCE ONLY. This file describes the old 107-task corpus and is not promotion evidence for the current 387-task generated corpus. There is no waiver path. Promotion requires a fresh full `val,test` run through `scripts/run_holzman_candidate_eval.py` with `non_promotable: false`, exact hashes, and hard `1.0` on both splits.

Candidate-only package. Live skills under `/home/lewis/.agents`, `/home/lewis/.opencode`, and `/home/lewis/.claude` were not modified.

## Dataset

- Generator: `scripts/generate_holzman_rust_dataset.py --seed 42`
- Dataset: `data/holzman_rust_aggressive`
- Total tasks: 107
- Split counts: train 64, val 21, test 22
- Split strategy: family-based split to reduce variant leakage.

## Training Evidence

- Smoke run: `reports/skillopt-training/holzman-smoke-seed-v2`
- Aggressive partial run: `reports/skillopt-training/holzman-aggressive-seed-v2`
- Aggressive run completed 43/48 planned steps before timeout.
- Aggressive SkillOpt best reached selection hard `0.80` at step 7, but final manual recipe candidate outperformed it on held-out test.

## Final Candidate Evaluation

- Full validation evidence: `reports/skillopt-training/holzman-aggressive-seed-v2/full_val_seed_recipes_v5`
- Full test evidence: `reports/skillopt-training/holzman-aggressive-seed-v2/full_test_seed_recipes_v5`
- Final split summary: `reports/skillopt-training/holzman-aggressive-seed-v2/final_candidate_eval_summary.json`
- Validation hard: 19/21 = `0.9047619047619048`, soft `0.9845238095238096`
- Test hard: 21/22 = `0.9545454545454546`, soft `0.9545454545454546`

## Targeted Post-Evaluation Checks

- Remaining full-run failures were rerun after tightening the candidate: `reports/skillopt-training/holzman-aggressive-seed-v2/targeted_remaining_seed_recipes_v6`
- Targeted hard: 3/3 = `1.0`, soft `1.0`
- These targeted checks were used as repair evidence, not as a replacement for the full split scores above.

## Promotion Status

- Do not promote automatically.
- Full validation and test are strong but not perfect, and one full test failure was a missing-output/stochastic OpenCode run.
- A live promotion requires another clean full validation/test pass on the current generated corpus.
