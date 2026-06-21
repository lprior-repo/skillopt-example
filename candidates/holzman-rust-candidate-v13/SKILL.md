---
name: holzman-rust-candidate-v13
description: "Candidate-only strict Holzman-first Functional Rust skill for Rust implementation, repair, review, and performance work. Keeps high-signal repair/review gates first, then aligns one-for-one with NASA/JPL Power-of-Ten, Functional Core / Imperative Shell, type-driven DDD, bounded resources, command-truth evidence, and measured performance."
---

# Holzman-First Functional Rust Candidate v13

Candidate-only. Do not promote without clean stress evidence against the current live Holzman skill.

## Absolute Laws

- No production `unsafe`, FFI, raw pointers, transmute-like tricks, unchecked access, unchecked arithmetic, lossy `as`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, production `assert!`, ignored fallible results, hidden I/O, invented command output, or fake benchmark evidence.
- These laws are not waivable in this candidate. If a task requires violating them, stop and report a blocker.
- Use safe Rust, typed errors, checked arithmetic, checked conversions, checked access, bounded resources, and explicit failure modes.
- Make illegal states unrepresentable with newtypes, enums, typestates, smart constructors, and domain errors.
- Parse hostile inputs once at boundaries into trusted domain values. Core logic consumes trusted types, not raw primitives.
- Keep calculations pure and deterministic. Put I/O, async, logging, metrics, clocks, randomness, persistence, retries, and environment access in the shell.

## Repair Mode

- Read tests and production source before editing. In eval/sandbox tasks, never edit tests or manifests unless explicitly allowed.
- Make the smallest production-source change satisfying behavior, domain model, typed errors, resource bounds, and strict lint gates.
- Before reporting done, inspect final source for missing `try_reserve`, unchecked `+`, unchecked `/`, lossy `as`, unchecked indexing/slicing, `unwrap`/`expect`/panic surfaces, `Vec::with_capacity`, `split(',').collect()`, `let _ = expr` on must-use values, hidden I/O, and changed tests/manifests.
- Run `cargo fmt`, `cargo test`, `cargo fmt --check`, and strict source `cargo clippy` when feasible. Never claim a command passed unless it actually passed.
- If JSON output is required, write the exact requested path and validate parseability when tools allow.
- In eval/sandbox mode, `reference_files_read` must list only the active `.skill/holzman-rust/...` bundle and task files you actually read. Never list `$HOME/.agents/...`, `$HOME/.opencode/...`, `$HOME/.claude/...`, or $HOME/.claude/..., or other live skill paths.

## Mandatory Repair Patterns

- CSV/parser-to-`Vec`: final source must contain `try_reserve` and must not contain `Vec::with_capacity`. Reject empty input first; do not collect split parts into a `Vec`; create `Vec::new`; call `values.try_reserve(max_items).map_err(|_| ParseError::Allocation)?` after cap validation; enforce max before each push with `if values.len() >= max_items { return Err(ParseError::TooMany); }`; parse with `map_err`; return typed `Empty`, `Invalid`, `TooMany`, `Overflow`, or `Allocation` errors. If a temporary collection is unavoidable, use `is_empty()`, never `len() == 0`.
- CSV/parser repair must not add a separate `count` variable with `count += 1`; strict clippy treats that as unchecked arithmetic. Prefer `values.len() >= max_items` before push. If a counter is truly required, increment only with `checked_add` and typed `Overflow`.
- If CSV/parser repair contains `let mut values = Vec::with_capacity(max_items);`, replace that exact line with `let mut values = Vec::new();` followed immediately by `values.try_reserve(max_items).map_err(|_| ParseError::Allocation)?;`. Do not report repaired while `Vec::with_capacity` remains or `try_reserve` is absent.
- If CSV/parser repair contains `let parts: Vec<...> = input.split(',').collect();` or `let parts: Vec<...> = input.split(',').map(...).collect();`, delete the `parts` vector. Iterate directly over `input.split(',')`, reserve `max_items` with `try_reserve`, and check `values.len() >= max_items` before each push.
- Frame/packet encoders: the final source must contain both `checked_add` and `try_reserve`; if either token is absent, the repair is incomplete even when tests and clippy pass. Do all four steps: check `payload.len() > max_payload`; compute `capacity = 4usize.checked_add(payload.len()).ok_or(FrameError::Overflow)?`; convert length with `u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?`; allocate with `Vec::new` then `out.try_reserve(capacity).map_err(|_| FrameError::Allocation)?`; then extend bytes.
- Summary/average code: use `line.split_once(',').ok_or(SummaryError::Invalid)?`; keep `count: usize`; increment only with `count = count.checked_add(1).ok_or(SummaryError::Overflow)?`; compare `count > max_rows` with no cast; derive `count_u64 = u64::try_from(count)` and `count_u32 = u32::try_from(count)`; compute `average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?`; return `Summary`; keep formatting in `render_summary`.
- Summary final source must contain both `u64::try_from(count)` and `u32::try_from(count)`. `count as u64`, `count as u32`, `try_into().unwrap_or(...)`, and “bounded by domain” cast arguments are failures.
- Never write `count += 1`, `max_rows as u64`, `count as u64`, `count as u32`, `total / count`, `line.split(',').collect()`, `input.split(',').collect()`, `parts.len() == 0`, `parts.get(...)`, `parts[i]`, `Vec::with_capacity` without fallible reserve, `let _ = name.trim()`, or `u64::from_str_radix(value_str.trim(), 10)` in strict source.
- For summary parsing, `split_once` is mandatory. `split(',').collect()`, `parts.len()`, and `parts.get()` are still allocation/shape mistakes even if they avoid panics.
- For unused split left fields, write exactly `let (_name, value_str) = line.split_once(',').ok_or(Error::Invalid)?;` and parse `value_str.trim().parse::<u64>()`. Do not bind `name` and then discard `name.trim()`. Do not use `from_str_radix(..., 10)`.

## Review Mode

- If the prompt requires a review JSON output file, create that file first and do not finish with an empty answer. The JSON file, not chat prose, is the success artifact. The JSON must parse and must contain `status`, `reference_files_read`, `findings`, `missing_evidence`, and `residual_risk`.
- Findings must be semantic and independently gradable: severity, rule, file, numeric `line`, construct, problem, concrete failure mode, smallest safe fix, and missing evidence.
- Every finding object must include `severity`, `rule`, `file`, numeric `line`, `problem`, `failure_mode`, and `fix`. If you cannot fill all required fields for a finding, omit it.
- Prefer 5-8 complete findings over 10+ findings. Extra findings are harmful if they omit required fields.
- Do not write keyword laundry; explain the reachable defect.
- Always flag present violations of panic surfaces, unchecked indexing/slicing, unchecked arithmetic/division, lossy casts, discarded must-use results, unbounded allocation, hidden I/O in pure logic, raw primitive domain state, unsupported performance claims, missing command evidence, and missing bounds.
- Typestate review: if a struct uses `status: String`, lifecycle booleans, or optional lifecycle fields, write exactly six complete findings: enum/typestate state machine, status/String, bool/lifecycle, Option invalid-state combinations, newtype/domain IDs, and a separate `parse_boundary` finding.
- The `parse_boundary` finding must literally contain both words `parse` and `boundary`: raw primitives cross the parse boundary without fallible smart constructors, so callers can construct invalid domain states directly.
- Hidden-I/O parser review: if file I/O, parsing, logging, allocation, and domain construction are fused, write 6-8 complete findings only: shell leakage, typed error taxonomy, unwrap/panic, unchecked access, lossy conversion, pure parsing/calculation boundary, and bounded allocation with `try_reserve`/domain caps. The bounded-allocation finding must literally include both `try_reserve` and `bounded` and say the fix is `Vec::new`, validate a domain cap/max rows first, then `try_reserve(cap)` before pushes.
- If review source has `line.split(',').map(...).collect()` into `parts` plus `parts[0]` or `parts[1]`, include an unchecked-access finding whose text literally contains `index`, `bounds`, `get`, and `split_once`. The fix is to avoid indexing with `line.split_once(',').ok_or(Error::Invalid)?` for two-field records, or use `parts.get(0)`/`parts.get(1)` with typed errors when a bounded vector is truly required.
- Tiny fixed-input performance review: if `[u8; 4]` or similarly tiny fixed data returns `Vec<&'static str>` or proposes Rayon/SmallVec by folklore, always flag Rayon/parallel overhead, SmallVec folklore, tiny fixed-size overhead, missing benchmark/baseline, allocation/Vec/collect, and recommend the literal fixed array return `[&'static str; 4]` or caller-owned output buffer unless measurement proves otherwise.
- Unsafe/SIMD review: any unsafe, unchecked slice/index, transmute-like conversion, raw pointer, or SIMD shortcut without a safe scalar path is a blocker. Do not propose unsafe as a fix.

## Doctrine Precedence And Claim Alignment

- Holzman Rust controls. Functional Rust is adopted only where it strengthens Holzman without weakening panic freedom, bounded control flow, bounded resources, source gates, command-truth evidence, or measured performance.
- This local skill is stricter than canonical Holzman on unsafe/FFI: no production unsafe, no FFI, no raw pointers, no transmute-like tricks, and no unchecked operations. There is no waiver path here.
- Simpler code wins when it satisfies the laws. Faster code wins only when measured and no law is weakened.
- In real-repo mode, read and list exact Holzman and Functional Rust references used. In eval/sandbox mode, read the active bundled skill, task source/tests, and bundled references present.

## Power-of-Ten Rust Claims

- Simple control flow: no recursion, panic-driven control flow, macro-hidden branching, or clever state hidden in closures; use explicit `match`, early typed returns, or named state machines.
- Bounded control flow: every loop, iterator pipeline, retry, traversal, stream poll, and worker drain needs a static upper bound, domain cap, or mathematical termination proof. Timeouts are containment, not proof.
- Allocation discipline: mission/safety-critical paths allocate only during initialization. Performance hot paths need allocation budgets, checked capacity arithmetic, fallible reserve where recovery matters, and benchmark/profiler evidence.
- Function size: hot/safety-critical functions target <=25 logical lines unless splitting hides invariants; all functions must stay one-page reviewable.
- Invariant density: encode invariants in types, constructors, parse boundaries, or checks returning typed errors. Production assertions are panic paths and forbidden except process-start invariant failure with clear diagnostics.
- Smallest scope: declare values near use; keep borrows, local mutability, locks, and temporary allocations narrow.
- Checked returns: never ignore `Result`, `Option`, join handles, channel sends, flushes, fallible cleanup, or must-use values.
- Macro/cfg discipline: macros, proc-macros, generated code, and conditional compilation must not hide allocation, panics, unsafe, loops, dispatch, or target-specific behavior.
- Static dispatch first: hot paths prefer generics, enums, direct calls, and monomorphization. `dyn Trait`, callbacks, function pointers, and heap indirection require runtime-polymorphism need plus measurement.
- Zero warnings: formatting drift, source clippy warnings, static-analysis findings, failing tests, and scoped policy gate failures block completion.

## Functional Rust Under Holzman

- Data/Calculations/Actions is mandatory architecture: Data is inert and valid, Calculations are pure and deterministic, Actions perform I/O and external effects.
- Parse-don't-validate: DTO/shell primitives are parsed once into trusted domain types; the core consumes trusted values.
- Domain APIs should not expose raw primitives when the value has rules. Use newtypes, enums, typestates, smart constructors, and explicit workflows.
- Replace status strings with enums. Replace lifecycle booleans with typestate transitions. Put optional lifecycle data inside the enum variant that owns it.
- Domain/core errors are typed. Shell boundaries may add context, but core logic must not collapse expected failures into strings or panics.
- Immutability and iterator pipelines are preferred only when they preserve Holzman analyzability. Bounded explicit loops and local `mut` are allowed when clearer, safer, or measured faster.
- Borrowed data, `Cow`, `Bytes`, zero-copy, `ArrayVec`, `SmallVec`, Rayon, and zero-heap designs are candidates, not defaults. Use them only when lifetime, size, workload, cache, and benchmark evidence justify them.
- Avoid intermediate `Vec`/`String` materialization unless materialization is required, bounded, and simpler than streaming.

## Performance And Runtime Architecture

- No performance claim without workload, target hardware, input distribution, hot path, baseline command, baseline number, new number, variance/noise notes, and regression threshold.
- Latency work reports p50/p95/p99 or max latency. Throughput work reports operations/sec, bytes/sec, requests/sec, items/sec, frames/sec, or another workload-specific rate.
- Storage placement must be justified by size, lifetime, locality, reuse, allocation cost, cache behavior, and tail-latency behavior.
- Optimize the measured bottleneck in order: algorithm, memory traffic, data layout, allocation, branch predictability, synchronization/syscalls, compiler visibility, then target-specific features.
- Prove slow, execute fast: proof, fuzzing, model checking, schema validation, graph validation, and semantic analysis happen before acceptance, not in production hot paths.
- Dense runtime IR is required when accepted human/spec/config data is repeatedly evaluated at runtime. Otherwise use dense IR only when measurement proves it beats the simpler representation.
- Claims about zero-cost abstractions, vectorization, bounds-check removal, public API compatibility, release provenance, or artifact integrity require second-ring evidence tied to actual symbols/artifacts.
- SIMD must be safe, have scalar fallback, target-feature gate, alignment/remainder handling, tests, and benchmark proof. If safe SIMD cannot satisfy the requirement, stop; do not use unsafe.

## Verification Gate

- Run the repository's canonical gate first.
- If no canonical gate exists, run or report blockers for:

```bash
cargo fmt --check
cargo check --workspace --all-targets --all-features
cargo clippy --workspace --lib --bins --examples --all-features -- -D warnings -D unsafe_code -D clippy::unwrap_used -D clippy::expect_used -D clippy::panic -D clippy::panic_in_result_fn -D clippy::todo -D clippy::unimplemented -D clippy::dbg_macro -D clippy::indexing_slicing -D clippy::string_slice -D clippy::get_unwrap -D clippy::arithmetic_side_effects -D clippy::as_conversions -D clippy::let_underscore_must_use -D clippy::await_holding_lock
cargo test --workspace --all-features --no-run
cargo test --workspace --all-features
```

- In real-repo mode, preserve the intent of `cargo audit`, `cargo deny check`, `cargo vet`, `cargo geiger`, `cargo machete`, `cargo hack`, `cargo mutants`, docs, nextest, and production panic-macro scans where available or required. Missing required tools are blockers or residual risk, not silent skips.
- Strict source linting excludes test targets as style gates, but tests/examples/benches must compile and tests must run.
- Classify failures as `BLOCK_LOCAL`, `BLOCK_REGRESSION`, `BLOCK_GLOBAL`, `REQUIRED_OBLIGATION_FAIL`, or `WAIVED_BY_USER_SPEC`. Local, regression, required-obligation, and global-readiness failures block delivery.

## Final Response

- List references read, changed files, commands actually run, failures/blockers, skipped checks, performance evidence, and residual risk.
- Never report success if required output files are missing, JSON is invalid, tests were edited in eval mode, commands failed, or an absolute law remains violated.
