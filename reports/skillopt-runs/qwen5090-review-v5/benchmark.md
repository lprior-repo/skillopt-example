# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-20T02:01:31.048825+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `reject`
- Current score: 1.000
- Best score: 1.000
- Best step: 0

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 6 | 1.000 | 1.000 | 1.000 | 6 |
| candidate-v5 | 6 | 1.000 | 1.000 | 1.000 | 6 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | review_unbounded_parser | review | 1.0 | 1.000 |  |
| baseline | review_async_cpu_mutex | review | 1.0 | 1.000 |  |
| baseline | review_unsafe_simd | review | 1.0 | 1.000 |  |
| baseline | review_dense_ir_hot_path | review | 1.0 | 1.000 |  |
| baseline | review_arithmetic_indexing | review | 1.0 | 1.000 |  |
| baseline | review_perf_claim_no_bench | review | 1.0 | 1.000 |  |
| candidate-v5 | review_unbounded_parser | review | 1.0 | 1.000 |  |
| candidate-v5 | review_async_cpu_mutex | review | 1.0 | 1.000 |  |
| candidate-v5 | review_unsafe_simd | review | 1.0 | 1.000 |  |
| candidate-v5 | review_dense_ir_hot_path | review | 1.0 | 1.000 |  |
| candidate-v5 | review_arithmetic_indexing | review | 1.0 | 1.000 |  |
| candidate-v5 | review_perf_claim_no_bench | review | 1.0 | 1.000 |  |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-review-v5/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-review-v5/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/qwen5090-review-v5/tasks`
