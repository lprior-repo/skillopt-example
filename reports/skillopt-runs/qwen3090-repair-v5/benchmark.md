# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T01:55:25.985182+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `accept_new_best`
- Current score: 0.610
- Best score: 0.610
- Best step: 1

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 6 | 0.167 | 0.850 | 0.508 | 1 |
| candidate-v5 | 6 | 0.333 | 0.886 | 0.610 | 2 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | repair_csv_u16 | repair | 0.0 | 0.883 | missing_groups=[['try_reserve', 'reserve']] |
| baseline | repair_checked_average | repair | 0.0 | 0.883 | missing_groups=[['try_from']] |
| baseline | repair_byte_at | repair | 1.0 | 1.000 |  |
| baseline | repair_frame_encoder | repair | 0.0 | 0.667 | missing_groups=[['try_reserve'], ['try_from']] |
| baseline | repair_remove_unsafe_copy | repair | 0.0 | 0.700 | missing_groups=[['to_vec', 'extend_from_slice'], ['get', 'split_at']] |
| baseline | repair_bounded_retries | repair | 0.0 | 0.967 | missing_groups=[['checked_shl'], ['try_reserve', 'reserve']] |
| candidate-v5 | repair_csv_u16 | repair | 0.0 | 0.900 |  |
| candidate-v5 | repair_checked_average | repair | 1.0 | 1.000 |  |
| candidate-v5 | repair_byte_at | repair | 1.0 | 1.000 |  |
| candidate-v5 | repair_frame_encoder | repair | 0.0 | 0.683 | missing_groups=[['try_reserve']] |
| candidate-v5 | repair_remove_unsafe_copy | repair | 0.0 | 0.950 |  |
| candidate-v5 | repair_bounded_retries | repair | 0.0 | 0.783 | missing_groups=[['try_reserve', 'reserve']] |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-v5/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-v5/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-v5/tasks`
