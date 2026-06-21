# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T01:47:57.832942+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `accept_new_best`
- Current score: 1.000
- Best score: 1.000
- Best step: 1

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.000 | 0.883 | 0.442 | 0 |
| candidate-v5 | 2 | 1.000 | 1.000 | 1.000 | 2 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | repair_csv_u16 | repair | 0.0 | 0.983 | missing_groups=[['try_reserve', 'reserve']] |
| baseline | repair_checked_average | repair | 0.0 | 0.783 | missing_groups=[['try_from']] |
| candidate-v5 | repair_csv_u16 | repair | 1.0 | 1.000 |  |
| candidate-v5 | repair_checked_average | repair | 1.0 | 1.000 |  |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v5/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v5/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-repair-smoke-v5/tasks`
