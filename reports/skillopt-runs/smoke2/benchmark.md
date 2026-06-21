# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-19T22:08:10.848036+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `reject`
- Current score: 1.000
- Best score: 1.000
- Best step: 0

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 1 | 1.000 | 1.000 | 1.000 | 1 |
| candidate-v1 | 1 | 0.000 | 0.500 | 0.250 | 0 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | review_unbounded_parser | review | 1.0 | 1.000 |  |
| candidate-v1 | review_unbounded_parser | review | 0.0 | 0.500 | missing_groups=[['typed error', 'result', 'parse error'], ['external input', 'untrusted input', 'boundary']]; json_invalid |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke2/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke2/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/smoke2/tasks`
