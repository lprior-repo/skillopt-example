# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T02:43:55.341630+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `reject`
- Current score: 0.700
- Best score: 0.700
- Best step: 0

## Promotion Gate

- Action: `reject`
- Blockers: skillopt_gate=reject, candidate_has_hard_failures

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.500 | 0.900 | 0.700 | 1 |
| candidate-v6 | 2 | 0.500 | 0.900 | 0.700 | 1 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | review_allocating_sensor_loader | review | 0.0 | 0.800 | missing_groups=[['Data/Calculations/Actions', 'actions layer', 'I/O boundary'], ['pure calculation', 'calculation layer', 'separate parsing']] |
| baseline | review_tiny_parallelism_overkill | review | 1.0 | 1.000 |  |
| candidate-v6 | review_allocating_sensor_loader | review | 0.0 | 0.800 | missing_groups=[['Data/Calculations/Actions', 'actions layer', 'I/O boundary'], ['pure calculation', 'calculation layer', 'separate parsing']] |
| candidate-v6 | review_tiny_parallelism_overkill | review | 1.0 | 1.000 |  |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-functional-review-v6/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-functional-review-v6/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-functional-review-v6/tasks`
