# Claim Alignment Research

Purpose: make the next candidate stronger by aligning every claim one-for-one with canonical Holzman Rust and Functional Rust, with Holzman Rust taking precedence whenever the doctrines conflict.

## Source Set

| Source | Path | Role |
|---|---|---|
| Canonical Holzman Rust | `/home/lewis/.agents/skills/holzman-rust/SKILL.md` | Primary doctrine and precedence source |
| Holzman OpenCode bridge | `/home/lewis/.opencode/skill/holzman-rust/SKILL.md` | Minimal live operational gate and bridge contract |
| NASA/JPL reference | `/home/lewis/.agents/skills/holzman-rust/references/nasa-jpl-standards.md` | Power-of-Ten mapping and PLUS gates |
| Runtime performance reference | `/home/lewis/.agents/skills/holzman-rust/references/runtime-performance-architecture.md` | Prove-slow/execute-fast, dense IR, hot-path shape |
| Functional Rust | `/home/lewis/.agents/skills/functional-rust/SKILL.md` | Functional core, DDD, zero-panic, zero-copy doctrine |
| Functional DDD reference | `/home/lewis/.agents/skills/functional-rust/references/scott-ddd-types.md` | DDD/type-level state modeling |
| Functional refactor checklist | `/home/lewis/.agents/skills/functional-rust/references/typing-refactor-checklist.md` | Primitive-to-type workflow and conflict points |
| Candidate under review | `candidates/holzman-rust-candidate-v11/SKILL.md` | Current candidate to strengthen |

## Precedence Rule

Holzman Rust wins every conflict. Functional Rust is accepted only when it strengthens or refines Holzman without weakening safety, bounded resources, command evidence, measured performance, or minimal correct change.

Concrete precedence decisions:

| Conflict | Holzman-First Resolution |
|---|---|
| Functional says no imperative loops; Holzman says simple bounded control flow | Bounded explicit loops are allowed when clearer, more analyzable, or faster; iterator pipelines are preferred only when equally bounded and readable. |
| Functional says Rayon/SmallVec/zero-copy first; Holzman says measure | Rayon, SmallVec, Cow, Bytes, zero-copy, and arrays require workload/size/lifetime/benchmark justification. No cargo-cult performance tools. |
| Functional says assertions for pre/postconditions; Holzman bans production panic paths | Use types, constructors, boundary checks, and typed errors. `debug_assert!` is supplemental only; production `assert!` is forbidden except process-start invariant failure with clear diagnostics. |
| Functional bans `mut`; Holzman allows narrow scope | Prefer immutability, but local `mut` is allowed for bounded buffers, checked loops, explicit state transitions, and measured hot paths. |
| Functional pushes Data/Calc/Actions; Holzman adds bounded and measured runtime | Data/Calc/Actions is the architecture, but hot paths must also satisfy Power-of-Ten bounds, allocation budgets, static dispatch, and measured storage placement. |
| Functional wants tests first; Holzman wants evidence gates | Tests are required behavior evidence, but final acceptance also needs fmt/check/clippy/test, scope classification, and risk-specific proof/fuzz/bench gates. |

## Claim Ledger

| ID | Holzman Claim | Functional Claim | v11 Coverage | Strengthening Needed |
|---|---|---|---|---|
| H01 | Reference files are fail-closed before Rust advice. | Functional references guide DDD/type migration. | Weak: v11 does not require reference listing. | Add “read and list exact Holzman + Functional refs used; fail closed if unavailable.” |
| H02 | Zero forbidden constructs: unsafe, unwrap, panic, unchecked access/arithmetic, ignored results. | No unwrap anywhere, no swallowed errors. | Strong. | Keep as first absolute law; mention `unwrap_or*` defaults are forbidden in domain core unless they encode an explicit policy. |
| H03 | Bounded control flow requires static bound or mathematical proof. | No imperative loops; iterator pipelines are naturally bounded. | Partial. | Add explicit claim: every loop, iterator pipeline, retry, traversal, stream, and worker drain needs a bound/proof. |
| H04 | No post-init dynamic allocation in critical paths; hot paths need allocation budget. | Zero heap first, avoid intermediate allocation. | Partial. | Add post-init/hot-path allocation budget claim and distinguish safety-critical vs performance-only hot paths. |
| H05 | Functions fit one page; target short hot functions. | One function one job, max around 60 lines. | Missing. | Add reviewability claim: target <=25 logical lines for hot/safety-critical functions unless splitting hides invariants. |
| H06 | Invariants exposed by types, constructors, checks returning typed errors. | Illegal states unrepresentable, parse-don’t-validate. | Strong. | Strengthen with “no production assert for invariants; typed recovery instead.” |
| H07 | Smallest scope; narrow borrows, mut, locks. | Zero mut by default. | Partial. | Add “immutability by default, narrow local mut permitted when clearer/measured.” |
| H08 | Check all returns and parameters. | No swallowed errors. | Partial. | Add explicit must-use list: `Result`, `Option`, join handles, sends, flushes, cleanup. |
| H09 | Macros must not hide allocation, panics, unsafe, loops, dispatch. | Linear flow, no deep nesting. | Missing. | Add macro/cfg/proc-macro claim. |
| H10 | Pointer/indirect calls restricted; static dispatch first in hot paths. | Prefer explicit workflows. | Partial. | Add static dispatch and no `dyn Trait`/callbacks in hot paths without measured need. |
| H11 | Zero warnings and static analysis block completion. | Warnings are errors. | Strong but fallback is smaller than canonical. | Add audit/deny/vet/geiger/machete/hack/mutants as required or reported blockers when in real-repo mode. |
| H12 | Scope-aware blocking: BLOCK_LOCAL, BLOCK_REGRESSION, BLOCK_GLOBAL, REQUIRED_OBLIGATION_FAIL. | Bead workflow references contract artifacts. | Missing. | Add classification model for gate failures. |
| H13 | Strict source lint excludes test targets, but tests compile/run and assert exact behavior. | Test style irrelevant; assertions exact; anti-tampering. | Partial. | Add exact test/source bifurcation and anti-tampering wording. |
| H14 | Performance claims need workload, hardware, baseline, numbers, variance, threshold. | Functional performance favors zero-copy, SmallVec, Rayon. | Strong. | Add p50/p95/p99 or throughput metrics by workload class. |
| H15 | Storage placement measured: stack/heap/arena/pool/static/caller-owned. | Zero-copy and zero-heap first. | Partial. | Add storage placement decision claim with measured size/lifetime/cache/tail-latency. |
| H16 | Dense IR mandatory for repeated runtime evaluation of accepted human/spec/config data. | Data/Calc/Actions compile domain to pure transitions. | Missing. | Add prove-slow/execute-fast and dense runtime IR claim. |
| H17 | Verification/proof/fuzz/model checking happen before hot path; runtime executes compact artifacts. | Pure calculations are deterministic. | Missing. | Add “proof slow, execute fast” claim with no validation/proof in hot path. |
| H18 | Safe SIMD only, scalar fallback, target-feature gate, benchmark proof. | Performance wants parallel/zero-copy. | Partial. | Add safe-SIMD-only claim; keep no unsafe/FFI local law stronger than canonical waiver language. |
| H19 | Pinned nightly and feature allowlist for nightly work. | Not covered. | Missing. | Add pinned toolchain policy if nightly is involved; forbid floating nightly and `RUSTC_BOOTSTRAP`. |
| H20 | Second-ring evidence for zero-cost, vectorization, bounds-check removal, API compatibility, release provenance. | Not covered. | Missing. | Add conditional second-ring evidence claim. |
| F01 | Data -> Calculations -> Actions layering. | Core doctrine. | Strong. | Keep, but tie each layer to Holzman bounds/evidence. |
| F02 | Parse boundary into zero-copy newtypes/Cow/Bytes. | Core doctrine. | Partial. | Add “prefer borrowed values where lifetimes are simple; ownership only when required/measured.” |
| F03 | No primitives in domain APIs. | Core doctrine. | Strong. | Keep; add exception: primitive at shell/DTO boundary is allowed only before parsing. |
| F04 | Enums/typestate for workflows. | Core doctrine. | Strong. | Keep; align with Holzman explicit state machines. |
| F05 | Core thiserror, shell anyhow/context. | Functional error discipline. | Missing. | Add “domain/core errors typed; shell may add context.” |
| F06 | No hidden side effects in helpers. | Core doctrine. | Strong. | Keep; add “hidden I/O is shell leakage and review blocker.” |
| F07 | No loops, iterator pipelines. | Conflicts with Holzman bounded simple loops. | v11 uses targeted patterns. | Replace blanket no-loop with Holzman-first “bounded loop or bounded iterator; choose clearer analyzable shape.” |
| F08 | No mut by default. | Soft conflict. | Missing nuance. | Add “immutable by default; local mut only with bounded scope and reason.” |
| F09 | Avoid intermediate collections. | Aligns with Holzman allocation discipline. | Strong in summary/parser patterns. | Generalize beyond CSV: no `collect` unless materialization is required and bounded. |
| F10 | Rayon for massive pure transforms. | Holzman requires measurement. | Strong-ish. | Say “Rayon only for large independent transforms with scaling evidence and bounded work.” |
| F11 | SmallVec for small predictable collections. | Holzman requires measured layout. | Strong-ish. | Say “ArrayVec for hard bounds; SmallVec only when small common case is measured and fallback allocation is acceptable.” |
| F12 | Tests first/alongside implementation. | Holzman requires evidence. | Partial. | Add behavior tests before/with code when changing behavior; never weaken tests. |

## Gaps In v11 That Prevent One-For-One Alignment

1. Reference-use claim is missing. Canonical Holzman requires fail-closed reference reads before implementation/review/performance advice.
2. Power-of-Ten rules are compressed into “absolute laws” but not individually represented: bounded control flow, post-init allocation, one-page functions, smallest scope, macro discipline, pointer/indirect call discipline.
3. Real-repo gate is too small versus canonical Holzman: it omits audit/deny/vet/geiger/machete/hack/mutants, doc, nextest, panic-macro scan, and scope classification.
4. Functional Rust conflicts are not explicitly resolved. The candidate should state where Functional Rust is subordinate: loops, Rayon, SmallVec, zero-copy, zero-heap, `mut`, and assertions.
5. Performance claims lack the full Holzman PLUS stack: latency/throughput budget, storage placement, allocation/layout/dispatch assumptions, dense IR, second-ring evidence, release provenance.
6. Core/shell error discipline is weaker than Functional Rust: candidate says typed errors but does not explicitly say domain/core errors are typed and shell errors may add context.
7. Tests/spec policy needs the shared source/test bifurcation: source style gates strict, tests compile/run/assert exact behavior, test style not a source lint gate.
8. Local “no FFI/no unsafe/no unchecked” law should be expressed as stricter-than-canonical. Canonical Holzman contains waiver language, but this project’s candidate must override it: no unsafe/FFI path here.

## Stronger Claim Wording For A v12 Candidate

Use these sections to make claims line up one-for-one while keeping v11’s eval-successful strictness.

### Supremacy And Reference Contract

```markdown
## Doctrine Precedence

Holzman Rust is the controlling doctrine. Functional Rust is adopted only where it strengthens Holzman without weakening bounded control flow, panic freedom, resource budgets, command-truth evidence, measured performance, or the local no-unsafe/no-FFI law. If they conflict, Holzman wins.

Before Rust implementation, repair, review, or performance advice, read and list the exact Holzman and Functional Rust references used. If required references are unavailable, stop and report a blocker instead of proceeding from memory.
```

### Power-of-Ten One-For-One Claims

```markdown
## Power-of-Ten Rust Claims

- Simple control flow: no recursion, panic-driven control flow, macro-hidden branching, or clever state hidden in closures; use explicit matches or named state machines.
- Bounded control flow: every loop, iterator pipeline, retry, traversal, stream poll, and worker drain needs a static upper bound or mathematical termination proof. Timeouts are containment, not proof.
- Allocation discipline: mission/safety-critical paths allocate only during initialization. Performance hot paths need allocation budgets, checked capacity arithmetic, fallible reserve where recovery matters, and benchmark/profiler evidence.
- Function size: hot/safety-critical functions target <=25 logical lines unless splitting hides invariants.
- Invariant density: encode invariants in types, constructors, parse boundaries, or checks returning typed errors. Production asserts are panic paths and forbidden except process-start invariant failure with clear diagnostics.
- Smallest scope: declare values near use; keep borrows, local mutability, locks, and temporary allocations narrow.
- Checked returns: never ignore `Result`, `Option`, join handles, sends, flushes, cleanup, or must-use values.
- Macro/pointer discipline: macros, cfg, proc-macros, trait objects, function pointers, and dynamic dispatch must not hide allocation, panics, unsafe, loops, or target behavior; hot paths prefer static dispatch.
- Zero warnings: fmt, check, strict source clippy, tests, static analysis, and repo policy gates block completion in scope.
```

### Functional Rust Under Holzman

```markdown
## Functional Rust Adoption

- Data/Calculations/Actions is mandatory architecture: Data is valid by construction, Calculations are pure deterministic functions, Actions own I/O and side effects.
- Parse-don't-validate: shell/DTO primitives are parsed once into domain types; the core consumes trusted types.
- Domain APIs should not expose raw primitives when the value has rules; use newtypes, enums, typestates, and smart constructors.
- Domain/core errors are typed. Shell boundaries may add context, but core logic must not collapse failures into strings or panics.
- Immutability and iterator pipelines are preferred only when they preserve Holzman analyzability. Bounded explicit loops and local `mut` are allowed when clearer, safer, or measured faster.
- Cow, Bytes, zero-copy, SmallVec, ArrayVec, Rayon, and zero-heap designs are candidates, not defaults. Holzman requires measured size/lifetime/cache/resource evidence before adopting them.
```

### Evidence And Gate Alignment

```markdown
## Evidence Gate

Run the repo canonical gate first. If absent, run the Holzman fallback gate or report blockers. In real-repo mode, preserve intent of audit/deny/vet/geiger/machete/hack/mutants/doc/nextest/panic-scan gates where available. Missing required tools are blockers or residual risk, not silent skips.

Classify failures as BLOCK_LOCAL, BLOCK_REGRESSION, BLOCK_GLOBAL, REQUIRED_OBLIGATION_FAIL, or WAIVED_BY_USER_SPEC. Local, regression, required-obligation, and global-readiness failures block delivery.
```

### Performance Alignment

```markdown
## Performance Claims

No performance claim without workload, target hardware, input distribution, hot path, baseline command, baseline number, new number, variance/noise notes, and regression threshold.

For latency work, report p50/p95/p99 or max latency. For throughput work, report operations/sec, bytes/sec, requests/sec, items/sec, or frames/sec. For storage placement, explain stack/heap/arena/pool/static/caller-owned choice by size, lifetime, locality, reuse, allocation cost, and tail-latency behavior.

Claims about zero-cost abstractions, vectorization, bounds-check removal, public API compatibility, or release provenance require second-ring evidence tied to actual symbols/artifacts.
```

## Recommended v12 Structure

1. Frontmatter and candidate warning.
2. Doctrine precedence and reference-use requirement.
3. Local absolute laws: no unsafe, no FFI, no unchecked status, no waiver path.
4. Power-of-Ten Rust claims, one bullet per canonical rule.
5. Functional Rust adoption under Holzman, with explicit conflict resolutions.
6. Repair mode with v11 high-performing repair patterns.
7. Review mode with v11 high-performing JSON/typestate/hidden-I/O/perf requirements.
8. Domain/resource rules generalized beyond the synthetic fixtures.
9. Performance claims and second-ring evidence.
10. Verification gate and failure classification.
11. Final response and evidence requirements.

## Bottom Line

The next strengthening should not add more recipes. It should add a traceable claim ledger inside the skill: every rule should say whether it comes from Holzman, Functional Rust, or Functional-under-Holzman. The strongest version is not “Holzman plus Functional”; it is “Holzman controls, Functional structures the core, and every Functional performance shortcut is gated by Holzman evidence.”
