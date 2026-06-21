# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- Prefer borrowed data, `Cow`, `Bytes`, caller-owned buffers, `split_once`, `get`, iterators, `try_fold`, checked arithmetic, checked division, checked shifts, `try_from`, and `try_reserve` when the failure mode requires them. Specifically, use `checked_*` methods for all arithmetic on sizes/counts, `try_from` for primitive conversions, and `try_reserve` for Vec allocation when size is known.
- Iterator chains and manual bounded loops are both allowed. Choose the clearer, safer, allocation-aware shape. Performance claims require workload, baseline, command, number, variance, and profiler/benchmark evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid.

## Repair Mode

Read tests and production source before editing. Do not edit tests. Make the smallest source change that satisfies tests and Holzman constraints. Run `cargo fmt`, then `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible. JSON command claims must match actual command outcomes. When allocating a Vec with known input size, prefer `try_reserve` over `with_capacity` to handle allocation failures.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.

## Repair Mode Specifics
- **Never edit test files.** Tests define the behavior contract. If tests fail, fix production code to match, or report that tests are incorrect (but do not modify them).
- When building a Vec from known/parseable input length, use `try_reserve` (or `try_from` for capacity) to handle allocation failures gracefully. Do not use `Vec::with_capacity` if the capacity might overflow or if you need to handle OOM.
- Use `try_from` for all primitive conversions (e.g., `usize` to `u32`) to prevent lossy casts. Use `checked_add`, `checked_mul`, etc. for arithmetic on lengths/capacities to prevent overflow.
- Verify command outputs before claiming success. If `cargo clippy` fails, do not claim it passed.

## Review Mode Specifics
- Flag any use of `Option<T>` or boolean flags (e.g., `is_valid: bool`) that encode state transitions or validity checks. Prefer typestate enums or newtypes to make illegal states unrepresentable.
- If a struct uses `Option` fields to represent "not yet set" or "optional" in a way that allows inconsistent states, flag it as a BLOCKER.
