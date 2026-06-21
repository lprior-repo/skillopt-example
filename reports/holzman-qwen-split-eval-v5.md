# Holzman Rust Qwen Split Eval Report

Generated: 2026-06-20

## What Was Evaluated

Target skill: `/home/lewis/.agents/skills/holzman-rust`.

Live skill edit policy: candidate-only. No live `.agents`, `.opencode`, or `.claude` Holzman files were modified.

Candidate selected by evidence: `candidates/holzman-rust-candidate-v5/`.

## How Evals Work

The harness is `scripts/holzman_skillopt_eval.py`.

For each task, it:

1. Creates a throwaway Rust crate from `evals/holzman-rust/tasks.json` under `/tmp/opencode/holzman-skillopt/<run-id>/...`.
2. Materializes two skill bundles: `baseline` from `/home/lewis/.agents/skills/holzman-rust`, and the selected candidate overlay.
3. Copies only the active bundle into each task sandbox as `.skill/holzman-rust`.
4. Calls OpenCode with `opencode run --pure --dir <sandbox> --agent build --model <pinned model>`.
5. Disables external skills, Claude skill compatibility, default plugins, and LSP during eval runs.
6. Grades task-local artifacts only.
7. Aggregates hard/soft scores and passes them through Microsoft SkillOpt's `evaluate_gate`.

Review grading requires valid task-local `review-output.json`, semantic finding coverage, no source mutation, and clean OpenCode execution.

Repair grading requires initial failure, preserved tests/Cargo.toml, valid `repair-output.json`, no forbidden production constructs, expected semantic repair groups, and passing `cargo fmt --check`, strict source `cargo clippy`, and `cargo test`.

This is a SkillOpt-style comparator, not full SkillOpt training. The SkillOpt research subagent confirmed real training would require a custom SkillOpt `EnvAdapter`, split dataset, rollout implementation, and `vendor/SkillOpt/scripts/train.py` loop.

## GPU/OpenCode Routing

Review model:

`qwen36-5090/Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`

Evidence observed:

- OpenCode model catalog labels it `Qwen3.6-35B 256k (5090 Local)`.
- Local endpoint: `http://127.0.0.1:11000/v1/models`.
- `nvidia-smi` showed `llama-server` PID `1505507` on GPU UUID `GPU-b2092e2c-3f30-482d-182b-17f3f6cda12c`, mapped to `NVIDIA GeForce RTX 5090`.

Repair/invocation model:

`qwen36-3090/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

Evidence observed:

- OpenCode model catalog labels it `Qwen3.6-35B 128k (3090 Local)`.
- Local endpoint: `http://127.0.0.1:11001/v1/models`.
- `nvidia-smi` showed `llama-server` PID `1638` on GPU UUID `GPU-403c2dbf-8f1c-f0d6-94a8-bd1fa4f6629f`, mapped to `NVIDIA GeForce RTX 3090`.

## 5090 Review Eval

Run: `reports/skillopt-runs/qwen5090-review-v5/`

Command:

```bash
.venv/bin/python scripts/holzman_skillopt_eval.py --run-id qwen5090-review-v5 --kind review --candidate-name candidate-v5 --candidate-overlay-dir candidates/holzman-rust-candidate-v5 --model qwen36-5090/Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf --timeout 600 --cargo-timeout 180
```

Result:

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 6 | 1.000 | 1.000 | 1.000 | 6 |
| candidate-v5 | 6 | 1.000 | 1.000 | 1.000 | 6 |

SkillOpt gate: `reject`, because candidate-v5 tied baseline.

Interpretation: candidate-v5 did not regress review behavior, but this split is saturated and gives no discriminative improvement signal.

## 3090 Repair Eval

Run: `reports/skillopt-runs/qwen3090-repair-v5/`

Command:

```bash
.venv/bin/python scripts/holzman_skillopt_eval.py --run-id qwen3090-repair-v5 --kind repair --candidate-name candidate-v5 --candidate-overlay-dir candidates/holzman-rust-candidate-v5 --model qwen36-3090/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf --timeout 900 --cargo-timeout 180
```

Result:

| Bundle | Tasks | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|---:|
| baseline | 6 | 0.167 | 0.850 | 0.508 | 1 |
| candidate-v5 | 6 | 0.333 | 0.886 | 0.610 | 2 |

SkillOpt gate: `accept_new_best`.

Candidate-v5 improved the repair split by `+0.102` mixed score and hard-passed one additional task.

## 5090 Final Review Of Candidate-v5

Run artifact: `reports/qwen5090-candidate-v5-final-review.md`.

5090 verdict: not ready for promotion.

Reasons:

- Candidate-v5 is focused and low-risk as an addendum.
- It improves repair behavior on the 3090 split.
- It does not regress review behavior.
- It still misses `try_reserve` on two full repair tasks despite explicit instruction.
- The eval has moderate overfitting risk because the smoke tasks overlap with the full repair split and the addendum targets exact observed failures.
- The current system is still a comparator, not automated SkillOpt training.

## Recommendation

Do not promote candidate-v5 into `/home/lewis/.agents/skills/holzman-rust` yet.

Candidate-v5 is the best candidate so far and should become the next baseline candidate for more evaluation, but it needs at least one independent held-out repair set and cross-model validation before live skill promotion.

Next concrete steps:

1. Add hidden or newly generated repair tasks that are not `csv_u16` or `checked_average` variants.
2. Run repair evals on both qwen36-3090 and qwen36-5090.
3. Run a true SkillOpt environment implementation if automated optimization, rather than candidate comparison, is the goal.
4. Only promote after candidate-v5 or a successor beats baseline on non-overlapping review and repair tasks without timeout or overfit evidence.
