# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- Use `checked_add`, `checked_sub`, `checked_mul`, `checked_div` for all arithmetic that can overflow. Use `try_from` for size conversions (e.g., `usize` to `u32`). Use `try_reserve` for `Vec` pre-allocation to handle allocation failures gracefully.
- Prefer borrowed data, `Cow`, `Bytes`, caller-owned buffers, `split_once`, `get`, iterators, `try_fold`, checked arithmetic, checked division, checked shifts, `try_from`, and `try_reserve` when the failure mode requires them.
- Iterator chains and manual bounded loops are both allowed. Choose the clearer, safer, allocation-aware shape. Performance claims require workload, baseline, command, number, variance, and profiler/benchmark evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid.

## Repair Mode

Read tests and production source before editing. **NEVER edit test files** (e.g., `tests/*.rs`, `*_test.rs`). Tests are the immutable behavior contract. Make the smallest source change that satisfies tests and Holzman constraints. Run `cargo fmt`, then `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible. **JSON command claims must match actual command outcomes.** If a command fails, report the failure and do not claim success.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.
