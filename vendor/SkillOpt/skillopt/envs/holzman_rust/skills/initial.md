# Optimized Holzman Rust Candidate

Use this skill for Rust implementation, repair, and review when the user wants high-reliability, high-performance Rust.

## Core Contract

- Make illegal states unrepresentable with newtypes, enums, typestates, and typed domain errors.
- Push logic into a pure deterministic core. Keep I/O, async, logging, persistence, clocks, randomness, retries, and external calls in the imperative shell.
- Parse at boundaries into trusted data. Do not repeatedly validate raw primitives inside the core.
- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, lossy `as`, ignored fallible results, or hidden side effects.
- Prefer borrowed data, `Cow`, `Bytes`, caller-owned buffers, `split_once`, `get`, iterators, `try_fold`, checked arithmetic, checked division, checked shifts, `try_from`, and `try_reserve` when the failure mode requires them.
- For `Vec`-producing parsers/encoders with a known maximum, compute capacity with checked arithmetic, call `try_reserve` before pushing/extending, and map allocation failure to a typed error such as `Allocation` when available.
- For frame encoders, summaries, and counters: use `checked_add` for sizes/totals, use `checked_div` after proving the divisor is nonzero, and use `u32::try_from`/`usize::try_from` instead of lossy width casts.
- For unsafe byte parsing, SIMD, unchecked slicing, or transmute-like shortcuts, require a safe scalar fallback or safe standard API (`from_le_bytes`, `get`, `split_at_checked` where available) plus explicit endian/bounds behavior.
- Iterator chains and manual bounded loops are both allowed. Choose the clearer, safer, allocation-aware shape. Performance claims require workload, baseline, command, number, variance, and profiler/benchmark evidence.

## Review Mode

Findings must be independently gradable: severity, rule, file, line, problem, concrete failure mode, and smallest compliant fix. Flag missing evidence as a finding. Review outputs requested as JSON must be valid. In reviews, explicitly call out missing bounded-allocation handling (`try_reserve`), missing checked capacity/summary arithmetic, missing checked conversions, and unsafe/SIMD paths without a scalar fallback.

## Repair Mode

Read tests and production source before editing. **NEVER edit test files** (`tests/*.rs`, `*_test.rs`, `tests/behavior.rs`). Tests are the immutable behavior contract. Make the smallest source change that satisfies tests and Holzman constraints. Run `cargo fmt`, then `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible. JSON command claims must match actual command outcomes; if a command fails, report the failure and do not claim success.

Before reporting a repair as done, check the source for these recurring misses: `Vec::with_capacity` without `try_reserve`, unchecked `+` in capacity/length/summary math, integer `/` where `checked_div` is required by the error taxonomy, `as` width casts instead of `try_from`, unchecked `parts[i]` indexing instead of `split_once`/`get`, and production tests or manifests changed unnecessarily.

## Repair Recipes

- CSV-to-`Vec` parsers: reject empty input first; create `Vec::new`; call `values.try_reserve(max_items).map_err(|_| ParseError::Allocation)?`; enforce `max_items` before pushing; parse with `map_err(|_| ParseError::Invalid)`; return `TooMany`, `Invalid`, and `Empty` exactly through the typed error taxonomy.
- Frame encoders: check `payload.len() > max_payload` before encoding; compute `capacity = 4usize.checked_add(payload.len()).ok_or(FrameError::Overflow)?`; convert length with `u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?`; allocate with `Vec::new` plus `try_reserve(capacity).map_err(|_| FrameError::Allocation)?`; then extend bytes.
- Summary/average repairs: do not collect split parts. Use `line.split_once(',').ok_or(SummaryError::Invalid)?`; parse with `map_err`; update totals and row counts with `checked_add`; convert count with `u64::try_from`/`u32::try_from`; compute average with `checked_div` after proving count is nonzero; return a `Summary` value and keep formatting in `render_summary`.
- Summary count pattern: keep `count: usize`, increment only with `count = count.checked_add(1).ok_or(SummaryError::Overflow)?`, compare `count > max_rows` with no cast, then derive `let count_u64 = u64::try_from(count).map_err(|_| SummaryError::Overflow)?; let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?; let average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?;`. Never write `count += 1`, `max_rows as u64`, `total / count`, or `count as u32`.
- Do not choose `count: u64` for summary row counts when `max_rows` is `usize`; it tempts `count as usize`. Keep `count: usize` until the final checked conversions. If an existing design forces `u64`, convert `max_rows` with `u64::try_from(max_rows).map_err(|_| SummaryError::Overflow)?`, never `as`.
- Summary split pattern: write `let (_name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;` and parse `value_str.trim()`. Never call `trim()` on the unused left field. Never write `let _ = name.trim();`; binding a `#[must_use]` result to `_` causes `clippy::let_underscore_must_use` failure, it does not silence it.
- Typestate reviews: when a struct combines `status: String`, lifecycle booleans, and optional timestamps, findings must mention enum/typestate state machine, invalid state combinations, newtype/domain IDs, and parse-boundary smart constructors.
- For typestate reviews, always include a distinct parse-boundary finding: rule `parse_boundary`, problem "raw primitives (`String`, `bool`, `Option`) enter the domain without a parse boundary/smart constructor", failure mode "callers can construct invalid states directly", fix "parse at the boundary into newtypes and enum variants through fallible constructors".
- For hidden-I/O CSV/parser reviews, always include a distinct bounded-allocation finding: rule `bounded_allocation`, problem "`collect::<Vec<_>>()`/`to_string()` allocates from unbounded input without `try_reserve` or a row/field cap", failure mode "large input can exhaust memory or panic/abort allocation", fix "parse with `split_once`, enforce a maximum, preflight result storage with `try_reserve`, and return a typed allocation error".
- Performance reviews for tiny fixed inputs: if a function takes `[u8; 4]` and returns `Vec`, call out the heap allocation and recommend a fixed array return such as `[&'static str; 4]` or a caller-owned output buffer unless measurement proves otherwise.

## Functional Core / Imperative Shell

Data is inert and valid by construction. Calculations are pure and deterministic. Actions perform I/O and side effects explicitly. Split only when it improves correctness, testability, or the requested behavior; do not over-refactor toy repairs.

## Performance Discipline

Do not cargo-cult Rayon, SmallVec, Cow, zero-copy, manual loops, or iterator chains. Use them because the workload, lifetime, allocation budget, or benchmark supports them. For tiny fixed-size inputs, avoid parallelism and heap collections unless measured.

## Verification

For real repositories, use the strongest repo gate. For isolated eval crates, obey the prompt-scoped gate and do not self-expand into audit/deny/vet/geiger/machete/hack/mutants/bench/doc/nightly gates unless asked.
