# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- Prefer borrowed data, `Cow`, `Bytes`, caller-owned buffers, `split_once`, `get`, iterators, `try_fold`, checked arithmetic, checked division, checked shifts, `try_from`, and `try_reserve` when the failure mode requires them.

- **Parsing:** Use `split_once` for first-delimiter extraction. Use `get` for indexed access. Never use `split` + `collect` + indexing when `split_once` suffices. Never use unchecked indexing like `parts[1]` without bounds checks.
- For `Vec`-producing parsers/encoders with a known maximum, compute capacity with `checked_add`/`checked_mul` (never unchecked `+`/`*`), call `try_reserve` (not `Vec::with_capacity`) before pushing/extending, and map allocation failure to a typed error such as `Allocation` when available.
- For frame encoders, summaries, and counters: use `checked_add`/`checked_mul` for sizes/totals/accumulators, use `checked_div` after proving the divisor is nonzero, and use `u32::try_from`/`usize::try_from` instead of lossy width casts.
- For unsafe byte parsing, SIMD, unchecked slicing, or transmute-like shortcuts, require a safe scalar fallback or safe standard API (`from_le_bytes`, `get`, `split_at_checked` where available) plus explicit endian/bounds behavior.
- Iterator chains and manual bounded loops are both allowed. Choose the clearer, safer, allocation-aware shape. Performance claims require workload, baseline, command, number, variance, and profiler/benchmark evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid. In reviews, explicitly call out missing bounded-allocation handling (`try_reserve`), missing checked capacity/summary arithmetic, missing checked conversions, and unsafe/SIMD paths without a scalar fallback.

## Repair Mode

Read tests and production source before editing. **NEVER edit test files** (`tests/*.rs`, `*_test.rs`, `tests/behavior.rs`). Tests are the immutable behavior contract. Make the smallest source change that satisfies tests and Holzman constraints. Run `cargo fmt`, then `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible. JSON command claims must match actual command outcomes; if a command fails, report the failure and do not claim success.

Before reporting a repair as done, check the source for these recurring misses: `Vec::with_capacity` without `try_reserve`, unchecked `+`/`*` in capacity/length/summary math (use `checked_add`/`checked_mul`), integer `/` where `checked_div` is required, `as` width casts instead of `try_from`, unchecked indexing instead of `split_once`/`get`, and production tests or manifests changed unnecessarily. Always prefer `try_reserve` over `Vec::with_capacity` when the capacity is bounded and allocation failure must be handled.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.
