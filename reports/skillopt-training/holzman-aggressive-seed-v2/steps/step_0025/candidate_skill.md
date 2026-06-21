# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- **Parsing & Access:** Use `split_once` for first-delimiter extraction. Use `get` for indexed access. Never use `split` + `collect` + indexing when `split_once` suffices. Never use unchecked indexing like `parts[1]` without bounds checks.
- **Allocation:** For `Vec` with known/bounded capacity, use `try_reserve` (not `with_capacity`) and handle `Allocation` errors. Compute capacity with `checked_add`/`checked_mul`.
- **Arithmetic:** Use `checked_add`/`checked_mul` for accumulators, `checked_div` for division (with non-zero check), and `try_from` for casts. Never use `as` for width changes or unchecked `+`/`/` for totals.
- **Safety:** No `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, or lossy `as`.
- **Performance:** Do not cargo-cult Rayon, SmallVec, Cow, or manual loops. Use them only with measured evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid.

**Review Completeness:** You must identify ALL violation categories present in the code (I/O in core, unwrap/panic, unchecked arithmetic, missing try_reserve, missing try_from, etc.). Do not stop after finding the first issue. Report all findings in the JSON output. Explicitly call out missing bounded-allocation handling (`try_reserve`), missing checked capacity/summary arithmetic, missing checked conversions, and unsafe/SIMD paths without a scalar fallback.

## Repair Mode

Read tests and production source before editing. **NEVER edit test files** (`tests/*.rs`, `*_test.rs`, `tests/behavior.rs`). Tests are the immutable behavior contract. Make the smallest source change that satisfies tests and Holzman constraints. Run `cargo fmt`, then `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible. JSON command claims must match actual command outcomes; if a command fails, report the failure and do not claim success.

**Holzman Safety Checklist (Verify before finalizing):**
1. **Allocation:** All bounded `Vec` constructions use `try_reserve` with error handling. Never use `Vec::with_capacity` for bounded allocations.
2. **Capacity Math:** All capacity calculations (e.g., `header + payload`) use `checked_add`/`checked_mul` and handle overflow.
3. **Arithmetic:** All integer division uses `checked_div` with non-zero check. All width-reducing casts use `try_from`/`TryInto::try_into`, never `as`.
4. **Parsing:** All delimiter extraction uses `split_once` or `get`. No unchecked indexing.
5. **Safety:** No `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, `unsafe`, or unchecked indexing.
6. **Claims:** All command status claims (fmt, test, clippy) match actual output. Never claim clippy passed if it produced warnings/errors.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.
