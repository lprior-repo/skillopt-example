# Holzman Rust SkillOpt Eval Run

Generated: 2026-06-19T23:32:09.712854+00:00

This run compares the current `.agents` Holzman Rust skill against a candidate-only evolved bundle. OpenCode executes review and repair tasks. Microsoft SkillOpt's validation gate decides whether the candidate beats the baseline on the mixed hard/soft metric.

## Gate

- Action: `reject`
- Current score: 0.650
- Best score: 0.650
- Best step: 0

## Aggregate Scores

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 12 | 0.417 | 0.883 | 0.650 | 5 |
| candidate-v1 | 12 | 0.500 | 0.656 | 0.578 | 6 |

## Task Scores

| Bundle | Task | Kind | Hard | Soft | Key Failures |
|---|---|---|---:|---:|---|
| baseline | review_unbounded_parser | review | 0.0 | 0.750 | missing_groups=[['unbounded', 'allocation', 'try_reserve', 'max']] |
| baseline | review_async_cpu_mutex | review | 1.0 | 1.000 |  |
| baseline | review_unsafe_simd | review | 1.0 | 1.000 |  |
| baseline | review_dense_ir_hot_path | review | 1.0 | 1.000 |  |
| baseline | review_arithmetic_indexing | review | 0.0 | 0.800 | missing_groups=[['external input', 'untrusted']] |
| baseline | review_perf_claim_no_bench | review | 1.0 | 1.000 |  |
| baseline | repair_csv_u16 | repair | 0.0 | 0.883 | missing_groups=[['try_reserve', 'reserve']] |
| baseline | repair_checked_average | repair | 0.0 | 0.783 | missing_groups=[['try_from']] |
| baseline | repair_byte_at | repair | 1.0 | 1.000 |  |
| baseline | repair_frame_encoder | repair | 0.0 | 0.667 | missing_groups=[['try_reserve'], ['try_from']] |
| baseline | repair_remove_unsafe_copy | repair | 0.0 | 0.725 | missing_groups=[['get', 'split_at']] |
| baseline | repair_bounded_retries | repair | 0.0 | 0.983 | missing_groups=[['try_reserve', 'reserve']] |
| candidate-v1 | review_unbounded_parser | review | 1.0 | 1.000 |  |
| candidate-v1 | review_async_cpu_mutex | review | 1.0 | 1.000 |  |
| candidate-v1 | review_unsafe_simd | review | 1.0 | 1.000 |  |
| candidate-v1 | review_dense_ir_hot_path | review | 1.0 | 1.000 |  |
| candidate-v1 | review_arithmetic_indexing | review | 1.0 | 1.000 |  |
| candidate-v1 | review_perf_claim_no_bench | review | 1.0 | 1.000 |  |
| candidate-v1 | repair_csv_u16 | repair | 0.0 | 0.217 | missing_groups=[['map_err', 'match'], ['try_reserve', 'reserve']]; forbidden=unwrap; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |
| candidate-v1 | repair_checked_average | repair | 0.0 | 0.317 | missing_groups=[['checked_add'], ['try_from']]; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |
| candidate-v1 | repair_byte_at | repair | 0.0 | 0.300 | missing_groups=[['get'], ['copied', 'cloned']]; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |
| candidate-v1 | repair_frame_encoder | repair | 0.0 | 0.217 | missing_groups=[['try_reserve'], ['try_from']]; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |
| candidate-v1 | repair_remove_unsafe_copy | repair | 0.0 | 0.500 | missing_groups=[['to_vec', 'extend_from_slice'], ['get', 'split_at']]; forbidden=unsafe; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |
| candidate-v1 | repair_bounded_retries | repair | 0.0 | 0.317 | missing_groups=[['checked_shl'], ['try_reserve', 'reserve']]; execution_errors=opencode_returncode=124,opencode_timeout; json_invalid |

## Artifacts

- Summary JSON: `/home/lewis/src/skill-moo/reports/skillopt-runs/full1/summary.json`
- Bundles: `/home/lewis/src/skill-moo/reports/skillopt-runs/full1/bundles`
- Per-task outputs: `/home/lewis/src/skill-moo/reports/skillopt-runs/full1/tasks`
