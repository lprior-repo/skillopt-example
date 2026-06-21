# Holzman Rust SkillOpt Optimization Report

Generated: 2026-06-19

## Scope

Target skill: `/home/lewis/.agents/skills/holzman-rust`.

Edit policy selected by user: candidate-only. No live `.agents`, `.opencode`, or `.claude` Holzman Rust files were modified.

Execution backend selected by user: OpenCode. The direct SkillOpt Azure/OpenAI environment variables were not present, so the harness used OpenCode model execution and Microsoft SkillOpt's validation gate as the acceptance comparator.

OpenCode model used for the full run: `minimax-coding-plan/MiniMax-M2.7-highspeed`.

## Subagents Used

- `general`: reviewed the OpenCode eval harness and found project-root leakage, output-path bugs, and fairness contamination.
- `general`: edited the candidate-only bundle to add eval-scope boundaries.
- `black-hat-reviewer`: adversarially reviewed the eval design and rejected the first harness as leaky/token-gameable.

## Candidate Bundle

Candidate path: `candidates/holzman-rust-candidate-v1/`

Candidate changes:

- Added `SKILL-addendum.md` with machine-readable review/repair output expectations and scope-boundary guidance.
- Added `references/evaluation-and-repair-protocol.md` with review/repair JSON contracts, repair ordering, and eval failure rules.

## Harness Repairs Before Full Run

The initial smoke run was contaminated because OpenCode executed from the repository root and the candidate read `evals/holzman-rust/tasks.json`. The harness was repaired before the full run:

- Each task crate now runs under `/tmp/opencode/holzman-skillopt/<run-id>/...`.
- Only the active skill bundle is copied into the sandbox as `.skill/holzman-rust`.
- OpenCode external skills and Claude skill compatibility are disabled for eval runs.
- OpenCode LSP is disabled for eval runs to prevent background `target/` and flycheck artifacts.
- Review grading reads only task-local `review-output.json`, not stdout/stderr token echoes.
- Repair grading requires `cargo fmt --check`, strict source `cargo clippy`, `cargo test`, protected tests/Cargo.toml, valid `repair-output.json`, no forbidden constructs, and expected semantic repair groups.
- The SkillOpt gate compares candidate and baseline mixed hard/soft scores.

## Full Evaluation

Run: `reports/skillopt-runs/full1/`

Command:

```bash
.venv/bin/python scripts/holzman_skillopt_eval.py --run-id full1 --model minimax-coding-plan/MiniMax-M2.7-highspeed --timeout 420 --cargo-timeout 180
```

Tasks:

- 6 review tasks.
- 6 repair tasks.
- Baseline and candidate both evaluated: 24 OpenCode executions total.

Aggregate result:

| Bundle | Hard | Soft | Mixed | Hard-Passed Tasks |
|---|---:|---:|---:|---:|
| baseline | 0.417 | 0.883 | 0.650 | 5/12 |
| candidate-v1 | 0.500 | 0.656 | 0.578 | 6/12 |

SkillOpt gate action: `reject`.

Interpretation: candidate-v1 improved review behavior but catastrophically failed repair behavior under this OpenCode/model setup, so it must not be promoted.

## Key Findings

- Candidate-v1 passed all 6 review tasks.
- Baseline passed 4 of 6 review tasks.
- Candidate-v1 timed out on all 6 repair tasks in `full1` before producing valid repair JSON.
- Baseline completed repair attempts and achieved high soft scores, but only hard-passed `repair_byte_at` because several repairs missed stricter semantic requirements like `try_reserve`, `try_from`, or `get`/`split_at`.
- A later one-task repair retry also timed out, so no further model budget was spent on retries.

## Promotion Decision

Do not promote candidate-v1 to `/home/lewis/.agents/skills/holzman-rust`.

Accepted evidence:

- The canonical baseline remains better by SkillOpt mixed score on the full eval.
- Candidate-v1's review-mode scope/output improvements are useful, but its repair-mode behavior is unstable enough to block promotion.

## Next Candidate Direction

For candidate-v2, keep review-specific improvements but do not require the extra evaluation protocol reference during normal repair. Instead:

- Move JSON/eval output guidance into an eval-only adapter note, not the general repair path.
- Add a compact repair checklist directly in `SKILL.md`: read tests, edit only source, run cargo test, run fmt/clippy, write requested output if present.
- Add explicit `try_reserve`, `try_from`, checked arithmetic, and safe-slice repair examples to references without adding a mandatory long-read path for every repair.
- Run review and repair evals separately to avoid conflating review gains with repair latency failures.
