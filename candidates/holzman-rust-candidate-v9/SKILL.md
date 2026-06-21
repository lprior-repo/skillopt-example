---
name: holzman-rust-candidate-v9
description: "Candidate-only strict Holzman Rust skill for Rust implementation, repair, review, and performance work. Enforces absolute no-unsafe/no-FFI/no-panic/no-unchecked-access laws, Functional Core / Imperative Shell, type-driven DDD, bounded resources, typed errors, command-truth evidence, and measured performance."
---

# Strict Holzman Rust Candidate v9

Candidate-only. Do not promote without clean full-run evidence against the current live skill.

## Absolute Laws

- No production `unsafe`, FFI, raw pointers, transmute-like tricks, unchecked access, unchecked arithmetic, lossy `as`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, production `assert!`, ignored fallible results, hidden I/O, invented command output, or fake benchmark evidence.
- These are laws, not preferences. Do not add waiver paths or workarounds for them. If existing code violates them and cannot be fixed in scope, report a blocker.
- Use safe Rust, typed errors, checked arithmetic, checked conversions, checked access, bounded resources, and explicit failure modes.
- Make illegal states unrepresentable with newtypes, enums, typestates, smart constructors, and domain errors.
- Parse hostile inputs once at boundaries into trusted domain values. Core logic consumes trusted types, not raw primitives.
- Keep calculations pure and deterministic. Put I/O, async, logging, metrics, clocks, randomness, persistence, retries, and environment access in the shell.

## First Pass

- Identify mode: review, repair, implementation, performance, eval/sandbox, or real repository.
- Read the active skill, references, production source, tests/specs, and manifests before claims or edits.
- Identify hostile inputs, resource caps, public API surface, side effects, and required output paths.
- State blockers early: missing files, missing tools, failing baseline gates, impossible scope, or absolute-law violations that cannot be fixed safely.

## Repair Mode

- In eval/sandbox tasks, do not edit tests or manifests unless explicitly allowed. In real repositories, never weaken tests; update tests only when the requested behavior/spec changed.
- Make the smallest production-source change that satisfies tests, domain safety, resource bounds, and strict lint gates.
- Preserve behavior unless the user/spec requires a change. Do not add compatibility shims without persisted data, public consumers, or explicit requirement.
- Before reporting done, scan the changed source for missing `try_reserve`, unchecked `+`, unchecked `/`, lossy `as`, unchecked indexing/slicing, `unwrap`/`expect`/panic surfaces, discarded must-use values, hidden I/O, and test/manifest edits.

## High-Frequency Repair Patterns

- CSV/parser-to-`Vec`: reject empty input first; validate an absolute domain cap before allocation; create `Vec::new`; call `try_reserve(validated_cap).map_err(|_| Error::Allocation)?`; enforce max before push; parse with `map_err`; return typed `Empty`, `Invalid`, `TooMany`, `Overflow`, or `Allocation` errors.
- Frame/packet encoders: check payload length against max before encoding; compute capacity with `checked_add`/`checked_mul`; convert lengths with `u32::try_from` or destination `try_from`; reserve with `try_reserve`; write bytes without unchecked indexing.
- Summary/average code: use `split_once` for one-separator grammar; keep `count: usize` while comparing with `max_rows`; increment with `checked_add`; convert with `u64::try_from` and `u32::try_from`; compute average with `checked_div`; return `Summary` data and keep rendering in `render_summary`.
- Never write `count += 1`, `max_rows as u64`, `count as u32`, `total / count`, `parts[i]`, `Vec::with_capacity` without fallible reserve, or `let _ = name.trim()` in strict source.
- For unused split left-hand values, write `let (_name, value_str) = line.split_once(',').ok_or(Error::Invalid)?;` and only parse `value_str.trim()`.

## Review Mode

- Findings must be semantic and independently gradable: severity, rule, file, line, construct, problem, concrete failure mode, smallest safe fix, and missing evidence.
- Do not write keyword-laundry. Explain the reachable defect.
- Always flag present violations of: panic surfaces, unchecked indexing/slicing, unchecked arithmetic/division, lossy casts, discarded must-use results, unbounded allocation, hidden I/O in pure logic, raw primitive domain state, unsupported performance claims, and missing command evidence.
- Typestate review: if a struct uses `status: String`, lifecycle booleans, or optional lifecycle fields, include separate findings for enum/typestate state machine, invalid state combinations, newtype/domain IDs, and parse-boundary smart constructors.
- Hidden-I/O parser review: if file I/O, parsing, logging, allocation, and domain construction are fused, include distinct findings for imperative-shell leakage, panic/error taxonomy, unchecked access, lossy conversion, and bounded allocation with `try_reserve`/domain caps.
- Tiny fixed-input performance review: if `[u8; 4]` or similarly tiny fixed data returns `Vec` or proposes Rayon/SmallVec by folklore, flag parallel overhead, allocation/Vec/collect, missing benchmark/baseline, and recommend a fixed array such as `[&'static str; 4]` or caller-owned output buffer unless measurement proves otherwise.
- If JSON output is required, write valid JSON to the exact requested path and read/parse it back when tools allow.

## Domain Modeling

- Replace status strings with enums.
- Replace lifecycle booleans with typestate transitions.
- Put optional lifecycle data inside the enum variant that owns it.
- Use newtypes for IDs, counters, bounded lengths, non-empty strings, ports, timestamps, units, and domain-specific numeric values.
- Smart constructors validate once at boundaries and return typed errors.
- Core APIs should express the domain workflow; primitive plumbing belongs at the boundary.

## Bounded Resource Policy

- Hostile-input growth needs a domain cap before allocation.
- Use checked capacity arithmetic before reserve.
- Prefer streaming, arrays, caller-owned buffers, `ArrayVec`, bounded queues, or incremental reserve when full collection is unnecessary.
- Treat `collect::<Vec<_>>()`, `to_string`, `format!`, `HashMap` growth, unbounded channels, recursion, retries, and task spawning as resource decisions that require a bound.

## Performance Discipline

- No performance claim without workload, baseline command, baseline number, new number, target hardware, variance/noise notes, and regression threshold.
- Optimize the measured bottleneck, not a guessed bottleneck.
- Stack, heap, arena, static storage, pools, caller-owned buffers, `SmallVec`, `ArrayVec`, `Bytes`, `Cow`, Rayon, SIMD, and zero-copy are tools, not defaults.
- SIMD must be safe, have scalar fallback, target-feature gate, alignment/remainder handling, tests, and benchmark proof. If safe SIMD cannot satisfy the requirement, stop; do not use unsafe.

## Async And Concurrency

- Async is for I/O concurrency, not CPU-heavy loops on runtime workers.
- Prefer ownership transfer, bounded channels, scoped tasks, sharding, atomics, or message passing over accidental `Arc<Mutex<_>>`.
- Holding locks across `.await`, unbounded task spawning, unbounded queues, and missing shutdown/drain paths are blockers.

## Verification Gate

- Run the repository's canonical gate first. If none exists, run or report blockers for:

```bash
cargo fmt --check
cargo check --workspace --all-targets --all-features
cargo clippy --workspace --lib --bins --examples --all-features -- -D warnings -D unsafe_code -D clippy::unwrap_used -D clippy::expect_used -D clippy::panic -D clippy::panic_in_result_fn -D clippy::todo -D clippy::unimplemented -D clippy::dbg_macro -D clippy::indexing_slicing -D clippy::string_slice -D clippy::get_unwrap -D clippy::arithmetic_side_effects -D clippy::as_conversions -D clippy::let_underscore_must_use -D clippy::await_holding_lock
cargo test --workspace --all-features --no-run
cargo test --workspace --all-features
```

- Strict source linting excludes test targets as style gates, but tests/examples/benches must compile and tests must run.
- Add proptest, fuzzing, Kani, Loom, Miri, sanitizers, dependency audit, or benchmarks when the risk profile requires them.

## Output Discipline

- If a prompt requires a file, write that exact file and validate it exists.
- If a prompt requires JSON, validate parseability and required fields before final response when tools allow.
- Final response must list completed work, commands actually run, failures/blockers, residual risk, and skipped checks.

## Promotion Boundary

Candidate v9 may inform live doctrine, but only selected changes should be merged after clean full validation/test, hash parity for the evaluated bundle, baseline comparison against the current live skill, and explicit human approval.
