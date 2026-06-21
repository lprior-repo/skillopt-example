# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T01:40:49.105231+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `accept_new_best`
- Current score: 0.442
- Best score: 0.442
- Best step: 1

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.000 | 0.833 | 0.417 | 0 |
| candidate-v3 | 2 | 0.000 | 0.883 | 0.442 | 0 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | repair_csv_u16 | repair | 0.0 | 0.983 | missing_groups=[['try_reserve', 'reserve']] |
| baseline | repair_checked_average | repair | 0.0 | 0.683 | missing_groups=[['try_from']] |
| candidate-v3 | repair_csv_u16 | repair | 0.0 | 0.983 | missing_groups=[['try_reserve', 'reserve']] |
| candidate-v3 | repair_checked_average | repair | 0.0 | 0.783 | missing_groups=[['try_from']] |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v3/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v3/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v3/tasks`
