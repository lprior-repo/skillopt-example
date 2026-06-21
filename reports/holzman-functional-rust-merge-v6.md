# Holzman + Functional Rust Merge Report

Generated: 2026-06-20

## Scope

Goal: pull `/home/lewis/.agents/skills/functional-rust` into the Holzman Rust candidate so the resulting skill focuses on writing fast, safe, functional-first Rust.

Live skill files were not modified. Work remained candidate-only.

New candidate:

`candidates/holzman-rust-candidate-v6/`

## Functional Rust Sources Used

- `/home/lewis/.agents/skills/functional-rust/SKILL.md`
- `/home/lewis/.agents/skills/functional-rust/references/scott-ddd-types.md`
- `/home/lewis/.agents/skills/functional-rust/references/typing-refactor-checklist.md`
- `/home/lewis/.agents/skills/functional-rust/references/complete-workflow.md`
- Prior best candidate: `candidates/holzman-rust-candidate-v5/`

## What Candidate-v6 Adds

- Functional Core / Imperative Shell: Data -> Calculations -> Actions.
- Parse-don't-validate boundary discipline.
- Typed domain states, newtypes, enums, typestates, and typed errors.
- Zero-copy and allocation-aware defaults: borrowed data, `Cow`, caller-owned buffers, lazy iterators, `try_fold`, and `try_reserve`.
- Performance precedence: no cargo-cult Rayon/SmallVec/manual-loop/iterator claims without workload and evidence.
- Conflict resolution: Holzman safety/evidence gates override Functional Rust preferences when they conflict.

New files:

- `candidates/holzman-rust-candidate-v6/SKILL-addendum.md`
- `candidates/holzman-rust-candidate-v6/references/functional-core-performance.md`
- `candidates/holzman-rust-candidate-v6/references/review-output-contract.md`

## New Eval Tasks Added

Added to `evals/holzman-rust/tasks.json`:

- `review_allocating_sensor_loader`: catches hidden I/O in parsing, allocation-heavy String/Vec usage, unchecked indexing, panic paths, lossy casts, and missing Data/Calculations/Actions separation.
- `review_tiny_parallelism_overkill`: catches performance folklore around Rayon/SmallVec on tiny fixed-size data without benchmark evidence.
- `repair_headers_zero_copy`: requires borrowed `Cow::Borrowed`, `split_once`, `try_reserve`, typed errors, and no panic indexing.
- `repair_metric_summary_layers`: requires pure `summarize_metrics`, shell `summarize_file`, `render_summary`, checked arithmetic, checked conversions, and separation of calculation from rendering/I/O.

## Eval Results

### 5090 Functional Review Split

Run: `reports/skillopt-runs/qwen5090-functional-review-v6/`

Command model:

`qwen36-5090/Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`

Result:

| Bundle | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|
| baseline | 0.500 | 0.900 | 0.700 | 1/2 |
| candidate-v6 | 0.500 | 0.900 | 0.700 | 1/2 |

SkillOpt comparator: `reject`.

Promotion gate: `reject`.

Interpretation: candidate-v6 did not improve the new functional review tasks. The model did catch many issues, but did not consistently use the exact Data/Calculations/Actions framing the rubric expected.

### 3090 Functional Repair Split

Run: `reports/skillopt-runs/qwen3090-functional-repair-v6/`

Command model:

`qwen36-3090/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

Result:

| Bundle | Hard | Soft | Mixed | Passed |
|---|---:|---:|---:|---:|
| baseline | 0.000 | 0.683 | 0.341 | 0/2 |
| candidate-v6 | 0.000 | 0.820 | 0.410 | 0/2 |

SkillOpt comparator: `accept_new_best`.

Promotion gate: `reject` because candidate-v6 has hard failures.

Interpretation: candidate-v6 improved repair soft score, but it still failed promotion gates. `repair_headers_zero_copy` passed tests/clippy but failed formatting. `repair_metric_summary_layers` edited protected tests and failed clippy due unchecked arithmetic/lossy conversion issues.

## Adversarial Review

The black-hat reviewer rejected candidate-v6 for promotion.

Critical issues:

- Mixed soft score can make a candidate look improved even when hard gates fail.
- Candidate-v6 did not consistently force reading `functional-core-performance.md`.
- Repair evidence included hard failures and false pass claims.
- Eval-specific recipes remain in the candidate addendum and should not be promoted as production skill text.

## Decision

Candidate-v6 successfully pulls in Functional Rust concepts into the candidate bundle, but it is not promotion-ready.

Do not copy candidate-v6 into `/home/lewis/.agents/skills/holzman-rust`.

## Next Work

1. Move eval-specific recipes out of production candidate text and into eval prompts.
2. Make `functional-core-performance.md` mandatory and grade `reference_files_read` for it.
3. Add semantic validators for Data/Calculations/Actions instead of fragile phrase matching.
4. Require promotion hard pass: no protected test edits, no fmt failure, no clippy failure, no false command claims.
5. Build the real SkillOpt `EnvAdapter` pipeline once candidate comparator behavior is stable.
