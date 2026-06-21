# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T01:37:09.041973+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `reject`
- Current score: 0.446
- Best score: 0.446
- Best step: 0

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.000 | 0.892 | 0.446 | 0 |
| candidate-v2 | 2 | 0.000 | 0.842 | 0.421 | 0 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | repair_csv_u16 | repair | 0.0 | 0.983 | missing_groups=[['try_reserve', 'reserve']] |
| baseline | repair_checked_average | repair | 0.0 | 0.800 |  |
| candidate-v2 | repair_csv_u16 | repair | 0.0 | 0.883 | missing_groups=[['try_reserve', 'reserve']] |
| candidate-v2 | repair_checked_average | repair | 0.0 | 0.800 |  |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v2/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v2/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v2/tasks`
