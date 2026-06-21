# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- **Holzman Safety Checklist:**
  1. **Parsing:** Use `split_once` for first-delimiter extraction. Use `get` for indexed access. Never use `split` + `collect` + indexing when `split_once` suffices.
  2. **Allocation:** For `Vec` with known/bounded capacity, use `try_reserve` (not `with_capacity`) and handle `Allocation` errors. Compute capacity with `checked_add`/`checked_mul`.
  3. **Arithmetic:** Use `checked_add`/`checked_mul` for accumulators, sizes, and totals. Use `checked_div` for division (with non-zero check). Use `try_from` for width casts. Never use `as` for width changes or unchecked `+`/`*`/`/` for totals.
  4. **Safety:** No `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, or lossy `as`.
  5. **Performance:** Do not cargo-cult Rayon, SmallVec, Cow, or manual loops. Use them only with measured evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid. In reviews, explicitly call out missing bounded-allocation handling (`try_reserve`), missing checked capacity/summary arithmetic, missing checked conversions, and unsafe/SIMD paths without a scalar fallback.

## Repair Mode

Read tests and production source before editing. **NEVER edit test files** (`tests/*.rs`, `*_test.rs`, `tests/behavior.rs`). Tests are the immutable behavior contract. Make the smallest source change that satisfies tests and Holzman constraints.

**Pre-Commit Safety Audit:**
Before finalizing, verify the source contains:
- `try_reserve` (not `with_capacity`) for any `Vec` with bounded capacity.
- `checked_add`/`checked_mul` for all accumulators, sizes, totals, and **capacity calculations**.
- `checked_div` for all divisions, with explicit non-zero checks.
- `try_from` for all width conversions (e.g., `usize` to `u32`).
- `split_once` or `get` for string field extraction, not manual indexing.
- No `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, or lossy `as`.

**Command Verification:**
Run `cargo fmt`, then `cargo test`. Run `cargo clippy` if feasible. **Do not claim success unless the command output explicitly confirms it.** If a command fails, report the failure, do not claim success, and do not fabricate output.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.
