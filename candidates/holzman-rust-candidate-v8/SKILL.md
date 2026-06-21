---
name: holzman-rust-candidate-v8
description: "Candidate-only high-assurance Rust skill for implementation, repair, review, unsafe/FFI triage, and performance work. Combines Holzmann/NASA Power-of-Ten discipline, Functional Core / Imperative Shell, type-driven DDD, bounded resources, command-truth evidence, and measured performance. Use for Rust code changes or reviews where panic freedom, allocation bounds, typed errors, safe APIs, and benchmark/proof evidence matter."
---

# Optimized Holzman Rust Candidate v8

Candidate-only skill. Do not treat this as promoted live doctrine until it has clean full validation against the current live baseline.

## Mission

Deliver Rust that is safe by construction, bounded under hostile input, honest about evidence, and fast only when measured. Safety beats cleverness. Evidence beats claims. Domain types beat repeated primitive validation. Simple code beats recipes copied into the wrong context.

## Operating Modes

- **Review mode**: inspect code and report semantic findings. Do not edit files unless explicitly asked.
- **Repair mode**: make the smallest source change that satisfies the behavior contract and the safety/performance constraints.
- **Implementation mode**: design the domain contract first, then write code, tests, and verification evidence.
- **Performance mode**: define workload, baseline, target hardware, threshold, command, and profiler evidence before optimizing.
- **Eval/sandbox mode**: obey the prompt-scoped output format and immutable fixture tests.
- **Real-repo mode**: use the repository's canonical gates and preserve external behavior unless the user/spec requires a change.

## First Pass Protocol

- Identify the mode, repository scope, touched crates/files, public API surface, and whether the task is eval/sandbox or real repo.
- Read production source, tests/specs, manifests, and relevant references before making claims or edits.
- Classify inputs as trusted, parsed-at-boundary, or hostile. Hostile inputs need size caps, typed errors, and resource budgets.
- Classify side effects as shell work: I/O, async, logging, metrics, clocks, randomness, persistence, network, retries, and environment access.
- State blockers early: missing files, missing tools, failing baseline gates, unavailable benchmark harnesses, or unsafe work needing waiver.

## Non-Negotiable Defaults

- No production `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing/slicing, unchecked arithmetic, lossy `as`, ignored fallible results, hidden I/O, or invented command output.
- Make illegal states unrepresentable with newtypes, enums, typestates, smart constructors, and typed domain errors when the invariant is real.
- Parse once at boundaries into trusted data. Do not let raw `String`, `bool`, `Option`, integers, paths, or byte slices roam through the core unchecked.
- Keep the pure core deterministic and side-effect free. Keep actions in the shell.
- Prefer small explicit state machines over clever closure/macro control flow.
- Use static dispatch and concrete data layout by default in hot paths. Use trait objects, heap indirection, and dynamic callbacks only with a reason.

## Waiver Policy

- Unsafe, FFI, raw pointers, unchecked access, `std::arch`, panic-as-control-flow, lossy casts, broad test rewrites, public API breaks, and speed-first nightly features require explicit user approval before code is written.
- A waiver must name the rule waived, the local preconditions, the postconditions, the tests/proofs/benchmarks that constrain it, and the residual risk.
- If a waiver is not granted, stop and report the blocker instead of quietly weakening the rule.

## Tests And Specs

- In eval/sandbox mode, test files are immutable unless the prompt explicitly allows edits.
- In real-repo mode, tests are not sacred if the requested behavior changed, but never silently weaken or delete assertions. Add or update tests only when they represent the user/spec behavior.
- Production source must not be shaped to satisfy weak tests while violating the domain contract.
- When tests and domain safety conflict, report the conflict and propose the smallest spec/test correction.

## Bounded Resource Policy

- Every hostile-input collection has an absolute domain cap before allocation or growth.
- Do not call `try_reserve(max_items)` until `max_items` is validated against a trusted `MAX_DOMAIN_*` cap or an input-derived upper bound.
- Use checked capacity arithmetic before reserve: `checked_add`, `checked_mul`, and typed `TooLarge`/`Overflow`/`Allocation` errors.
- Prefer streaming, caller-owned buffers, arrays, `ArrayVec`, bounded queues, or incremental reserve when a full collection is not required.
- Treat `collect::<Vec<_>>()`, `to_string`, `format!`, `HashMap` growth, unbounded channels, recursion, retries, and worker spawning as resource decisions that need a bound.

## Domain Modeling Rules

- Replace status strings plus lifecycle booleans with enums or typestate transitions.
- Put optional lifecycle data inside the enum variant that owns it, not as a global `Option` field that permits invalid combinations.
- Use newtypes for IDs, counters, bounded lengths, non-empty strings, paths, ports, timestamps, and units when the value has domain rules.
- Smart constructors should validate once and return typed errors. Core logic should consume already-valid domain types.
- Error taxonomies should be railway-friendly: expected domain failures are typed variants, not panics or strings.

## Review Contract

- Findings must be semantic, not keyword laundry.
- Each finding must include severity, rule, file, line, actual construct, concrete failure mode, smallest safe fix, and missing evidence when relevant.
- A finding is weak if it only says "use try_reserve" or "use typestate" without explaining the reachable failure.
- Reviews must call out missing parse boundaries, invalid-state representations, unbounded allocation, hidden side effects, panic paths, unchecked arithmetic/access, lossy conversions, unsafe/FFI obligations, and unsupported performance claims when present.
- For required JSON output, write only valid JSON to the requested path and read/parse it back when the host tools allow it.

## Repair Contract

- Make the smallest production-source change that satisfies behavior, type safety, resource bounds, and verification.
- Do not hide failures with broad `String` errors when a typed error already exists or is warranted by the domain.
- Do not add compatibility shims unless persisted data, public API consumers, or the user require them.
- Run formatting before tests. Run the repo gate or fallback gate before claiming success.
- Never claim a command passed unless it actually ran and passed. If a command fails, report the exact failure and whether it is local, regression, or pre-existing global.

## Implementation Contract

- Start from the domain workflow and invariants, not from primitives.
- Design value objects, state transitions, typed errors, and shell boundaries before writing hot-path mechanics.
- Keep functions short enough to review. Split when it exposes an invariant or prevents accidental side effects.
- Avoid framework, dependency, or architecture changes unless they are the smallest correct solution.
- Public API changes require rationale and migration impact.

## Performance Contract

- No performance claim without workload, baseline command, baseline number, new number, target hardware, variance/noise notes, and regression threshold.
- Optimize the measured bottleneck, not a guessed bottleneck.
- Stack, heap, arena, static, pool, caller-owned buffer, `SmallVec`, `ArrayVec`, `Bytes`, `Cow`, Rayon, SIMD, and zero-copy are tools, not defaults.
- For tiny fixed-size inputs, prefer arrays or caller-owned buffers over heap `Vec` unless measurement proves otherwise.
- SIMD requires scalar oracle, scalar fallback, target-feature gate, alignment/remainder handling, tests, and benchmark proof. Unsafe SIMD requires waiver.

## Unsafe, FFI, And Low-Level Boundaries

- Default to safe Rust and safe crates.
- FFI wrappers must validate nullability, alignment, length, lifetime, ownership, aliasing, initialization, thread-safety, and unwind behavior.
- Any safe wrapper around unsafe internals needs documented invariants and tests that exercise boundary failures.
- `repr(C)`, `repr(transparent)`, packed layout, transmute-like conversions, and pointer arithmetic require ABI/layout evidence.

## Async And Concurrency

- Async is for I/O concurrency, not CPU-heavy loops on runtime workers.
- Prefer ownership transfer, bounded channels, scoped tasks, sharding, atomics, or message passing over accidental `Arc<Mutex<_>>`.
- Holding locks across `.await`, unbounded task spawning, unbounded queues, and missing shutdown/drain paths are blockers.
- Concurrent code needs deterministic tests or model/stress evidence when schedules can change correctness.

## Verification Gate

- Run the repository's canonical gate first.
- If no stronger gate exists, use this fallback for Rust code work and report exact blockers if unavailable:

```bash
cargo fmt --check
cargo check --workspace --all-targets --all-features
cargo clippy --workspace --lib --bins --examples --all-features -- -D warnings -D unsafe_code -D clippy::unwrap_used -D clippy::expect_used -D clippy::panic -D clippy::panic_in_result_fn -D clippy::todo -D clippy::unimplemented -D clippy::dbg_macro -D clippy::indexing_slicing -D clippy::string_slice -D clippy::get_unwrap -D clippy::arithmetic_side_effects -D clippy::as_conversions -D clippy::let_underscore_must_use -D clippy::await_holding_lock
cargo test --workspace --all-features --no-run
cargo test --workspace --all-features
```

- Strict source linting excludes test targets as style gates, but tests/examples/benches must compile and tests must run.
- Add proptest, fuzz, Kani, Loom, Miri, sanitizers, audit/deny/geiger/vet, or benchmark gates when the risk profile requires them.

## Required Output Discipline

- If the prompt asks for a file output, write that exact file path and validate that it exists before final response.
- If the prompt asks for JSON, validate parseability and required top-level fields before final response when tools allow it.
- Final responses must separate completed work, commands actually run, failures/blockers, residual risk, and skipped checks.

## Anti-Regression Patterns

- Parser-to-collection code should reject empty or malformed input through typed errors, enforce a domain cap, preflight bounded storage with `try_reserve`, and map allocation failure.
- Encoders should check payload bounds, use checked capacity arithmetic, convert lengths with `try_from`, reserve fallibly, and write bytes without unchecked indexing.
- Summary/average code should parse with `split_once`, keep counts in a type that avoids casts against the max bound, increment with `checked_add`, convert with `try_from`, and divide with `checked_div`.
- Do not discard `#[must_use]` results with `let _ = expr`; either use the result, bind the original unused value as `_name`, or remove the call.
- Typestate reviews should include separate findings for state-machine shape, lifecycle booleans, optional invalid-state fields, newtype/domain IDs, and parse-boundary smart constructors when those defects exist.
- Hidden-I/O parser reviews should include bounded-allocation and side-effect findings when parsing, reading files, logging, and allocation are fused.
- Tiny fixed-input performance reviews should consider fixed arrays or caller-owned buffers before heap collections.

## Promotion Boundary

This candidate can inform a live skill, but it is not itself promotion-safe without clean full-run evidence, hash parity for the evaluated bundle, baseline comparison against the current live skill, and explicit human approval.
