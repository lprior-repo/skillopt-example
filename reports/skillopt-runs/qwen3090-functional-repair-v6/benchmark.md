# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T02:43:55.540635+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `accept_new_best`
- Current score: 0.410
- Best score: 0.410
- Best step: 1

## Promotion Gate

- Action: `reject`
- Blockers: candidate_has_hard_failures

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 2 | 0.000 | 0.683 | 0.341 | 0 |
| candidate-v6 | 2 | 0.000 | 0.820 | 0.410 | 0 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | repair_headers_zero_copy | repair | 0.0 | 0.686 | missing_groups=[['split_once'], ['try_reserve']] |
| baseline | repair_metric_summary_layers | repair | 0.0 | 0.680 | missing_groups=[['read_to_string', 'summarize_file'], ['split_once'], ['try_fold', 'fold'], ['u32::try_from', 'try_from']] |
| candidate-v6 | repair_headers_zero_copy | repair | 0.0 | 0.900 |  |
| candidate-v6 | repair_metric_summary_layers | repair | 0.0 | 0.740 | missing_groups=[['try_fold', 'fold'], ['u32::try_from', 'try_from']]; protected_changed=tests/behavior.rs |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-functional-repair-v6/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-functional-repair-v6/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen3090-functional-repair-v6/tasks`
