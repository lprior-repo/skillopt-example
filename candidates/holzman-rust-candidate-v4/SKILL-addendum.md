## Review And Repair Eval Hardening

This addendum strengthens the canonical Holzman Rust doctrine without weakening any existing Power-of-Ten, unsafe, panic-free, benchmark, or verification gate. It is intentionally small: repair tasks must stay fast and source-focused.

### Scope Boundary

When a prompt names a target crate, file list, workspace, or output path, treat that as a hard boundary after reading the prompt-named skill bundle and required references. Do not inspect parent directories, sibling eval tasks, repo-level `evals/**`, candidate overlays, reports, or manifests unless the prompt explicitly names them as targets.

If the named target or output path is unavailable, report that blocker. Do not substitute another task list or widen scope.

### Review Mode

When asked to review Rust code, produce findings that are independently gradable:

- Name the exact rule violated.
- Cite file and line when available.
- State the concrete failure mode, not just the banned token.
- Separate `BLOCKER`, `MAJOR`, and `MINOR` severity.
- Include the smallest compliant fix direction.
- Record missing benchmark, profiler, second-ring, or command evidence as a finding, not as approval.
- If machine-readable JSON is requested, write exactly the requested file and keep it valid.
- When machine-readable review output is requested, read `references/review-output-contract.md` if it is present in the active skill bundle.

### Repair Fast Path

When asked to repair Rust code:

1. Read the canonical skill and only the references needed for the observed failure.
2. Read `Cargo.toml`, production source, and tests before editing.
3. Do not edit tests unless the user explicitly asks for test repair.
4. Make the smallest production-source change that satisfies tests and Holzman constraints.
5. Prefer typed errors, `get`/iterator/chunk access, `checked_*`, `try_from`, bounded allocation, and `try_reserve` where the failure mode requires them.
6. For untrusted or max-bounded `Vec`/`String` growth, use literal `try_reserve` before pushing. `Vec::with_capacity` alone is not acceptable in eval repair output because allocation failure is not handled.
7. For length or offset conversions, use literal `u32::try_from`, `usize::try_from`, or the destination type's `try_from`. Never use `as` in production repair output.
8. For strict `clippy::arithmetic_side_effects`, use checked arithmetic for addition, multiplication, shifts, and division. After proving a denominator is nonzero and converting it with `try_from`, prefer `checked_div(...).ok_or(Error::Overflow)?` over raw `/`.
9. Run `cargo fmt` after editing, then run the requested gate, or at minimum `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible.
10. If machine-readable JSON is requested, write exactly the requested file after the commands run.

Do not turn a small repair into an open-ended eval-system audit unless the prompt asks for that audit.

For throwaway/eval repair prompts that name a target crate and output path, the prompt's requested command set is the gate. Do not run `cargo audit`, `cargo deny`, `cargo vet`, `cargo geiger`, `cargo machete`, `cargo hack`, `cargo mutants`, benchmarks, docs, repo-wide gates, nightly gates, or supply-chain gates unless explicitly requested.
