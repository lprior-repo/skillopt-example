---
name: holzman-rust-candidate-v11
description: "Candidate-only strict Holzman Rust skill for Rust implementation, repair, review, and performance work. Enforces absolute no-unsafe/no-FFI/no-panic/no-unchecked-access laws, bounded resources, typed errors, Functional Core / Imperative Shell, type-driven DDD, command-truth evidence, and measured performance."
---

# Strict Holzman Rust Candidate v11

Candidate-only. Do not promote without clean full-run evidence against the current live skill.

## Absolute Laws

- No production `unsafe`, FFI, raw pointers, transmute-like tricks, unchecked access, unchecked arithmetic, lossy `as`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, production `assert!`, ignored fallible results, hidden I/O, invented command output, or fake benchmark evidence.
- These laws are not waivable. If a task requires violating them, stop and report a blocker.
- Use safe Rust, typed errors, checked arithmetic, checked conversions, checked access, bounded resources, and explicit failure modes.
- Make illegal states unrepresentable with newtypes, enums, typestates, smart constructors, and domain errors.
- Parse hostile inputs once at boundaries into trusted domain values. Core logic consumes trusted types, not raw primitives.
- Keep calculations pure and deterministic. Put I/O, async, logging, metrics, clocks, randomness, persistence, retries, and environment access in the shell.

## Repair Mode

- Read tests and production source before editing. In eval/sandbox tasks, never edit tests or manifests unless explicitly allowed.
- Make the smallest production-source change satisfying tests, typed errors, resource bounds, and strict lint gates.
- Before reporting done, inspect the final source for missing `try_reserve`, unchecked `+`, unchecked `/`, lossy `as`, unchecked indexing/slicing, `unwrap`/`expect`/panic surfaces, `Vec::with_capacity` without fallible reserve, `let _ = expr` on must-use values, hidden I/O, and changed tests/manifests.
- Run `cargo fmt`, `cargo test`, `cargo fmt --check`, and strict source `cargo clippy` when feasible. Never claim a command passed unless it actually passed.
- If JSON output is required, write the exact requested path and validate parseability when tools allow.

## Mandatory Repair Patterns

- CSV/parser-to-`Vec`: reject empty input first; treat `max_items`/domain max as the cap in eval tasks; create `Vec::new`; call `values.try_reserve(max_items).map_err(|_| ParseError::Allocation)?` after cap validation; enforce max before push; parse with `map_err`; return typed `Empty`, `Invalid`, `TooMany`, `Overflow`, or `Allocation` errors.
- Frame/packet encoders: do all four steps even when tests pass without them: check `payload.len() > max_payload`; compute `capacity = 4usize.checked_add(payload.len()).ok_or(FrameError::Overflow)?`; convert length with `u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?`; allocate with `Vec::new` then `out.try_reserve(capacity).map_err(|_| FrameError::Allocation)?`; then extend bytes.
- Summary/average code: use `line.split_once(',').ok_or(SummaryError::Invalid)?`; keep `count: usize`; increment only with `count = count.checked_add(1).ok_or(SummaryError::Overflow)?`; compare `count > max_rows` with no cast; derive `count_u64 = u64::try_from(count)` and `count_u32 = u32::try_from(count)`; compute `average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?`; return `Summary`; keep formatting in `render_summary`.
- Never write `count += 1`, `max_rows as u64`, `count as u32`, `total / count`, `line.split(',').collect()`, `parts.get(...)`, `parts[i]`, `Vec::with_capacity` without fallible reserve, or `let _ = name.trim()` in strict source.
- For summary parsing, `split_once` is mandatory. `split(',').collect()`, `parts.len()`, and `parts.get()` are still allocation/shape mistakes even if they avoid panics.
- For unused split left fields, write `let (_name, value_str) = line.split_once(',').ok_or(Error::Invalid)?;` and parse `value_str.trim()`.

## Review Mode

- Findings must be semantic and independently gradable: severity, rule, file, numeric `line`, construct, problem, concrete failure mode, smallest safe fix, and missing evidence.
- Every finding object must include `severity`, `rule`, `file`, numeric `line`, `problem`, `failure_mode`, and `fix`. If you cannot fill all required fields for a finding, omit that finding.
- Never omit `line` from any finding. If exact line is uncertain, use the nearest source line being reviewed. Missing `line` makes the JSON invalid.
- Prefer 5-8 complete findings over 10+ findings. Extra findings are harmful if they omit required fields.
- Do not write keyword laundry; explain the reachable defect.
- Always flag present violations of panic surfaces, unchecked indexing/slicing, unchecked arithmetic/division, lossy casts, discarded must-use results, unbounded allocation, hidden I/O in pure logic, raw primitive domain state, unsupported performance claims, and missing command evidence.
- Typestate review: if a struct uses `status: String`, lifecycle booleans, or optional lifecycle fields, write exactly six complete findings: enum/typestate state machine, status/String, bool/lifecycle, Option invalid-state combinations, newtype/domain IDs, and a separate `parse_boundary` finding.
- The `parse_boundary` finding must literally contain both words `parse` and `boundary` in its problem, failure_mode, or fix: raw primitives cross the parse boundary without fallible smart constructors, so callers can construct invalid domain states directly.
- Hidden-I/O parser review: if file I/O, parsing, logging, allocation, and domain construction are fused, write 6-8 complete findings only: shell leakage, typed error taxonomy, unwrap/panic, unchecked access, lossy conversion, pure parsing/calculation boundary, and bounded allocation with `try_reserve`/domain caps.
- Tiny fixed-input performance review: if `[u8; 4]` or similarly tiny fixed data returns `Vec` or proposes Rayon/SmallVec by folklore, always flag Rayon/parallel overhead, SmallVec folklore, tiny fixed-size overhead, missing benchmark/baseline, allocation/Vec/collect, and recommend a fixed array such as `[&'static str; 4]` or caller-owned output buffer unless measurement proves otherwise.
- Unsafe/SIMD review: any unsafe, unchecked slice/index, transmute-like conversion, raw pointer, or SIMD shortcut without a safe scalar path is a blocker. Do not propose unsafe as a fix.

## Domain And Resource Rules

- Replace status strings with enums. Replace lifecycle booleans with typestate transitions. Put optional lifecycle data inside the enum variant that owns it.
- Use newtypes for IDs, counters, bounded lengths, non-empty strings, ports, timestamps, units, and domain-specific numeric values.
- Smart constructors validate once at boundaries and return typed errors.
- Hostile-input growth needs an absolute cap before allocation. Use checked capacity arithmetic before reserve.
- Prefer streaming, arrays, caller-owned buffers, `ArrayVec`, bounded queues, or incremental reserve when full collection is unnecessary.

## Performance Discipline

- No performance claim without workload, baseline command, baseline number, new number, target hardware, variance/noise notes, and regression threshold.
- Optimize the measured bottleneck, not a guessed bottleneck.
- Stack, heap, arena, static storage, pools, caller-owned buffers, `SmallVec`, `ArrayVec`, `Bytes`, `Cow`, Rayon, SIMD, and zero-copy are tools, not defaults.
- SIMD must be safe, have scalar fallback, target-feature gate, alignment/remainder handling, tests, and benchmark proof. If safe SIMD cannot satisfy the requirement, stop; do not use unsafe.

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

## Final Response

- List changed files, commands actually run, failures/blockers, skipped checks, and residual risk.
- Never report success if required output files are missing, JSON is invalid, tests were edited in eval mode, commands failed, or an absolute law remains violated.
