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
6. Run `cargo fmt` after editing, then run the requested gate, or at minimum `cargo test`; run `cargo fmt --check` and strict source `cargo clippy` when feasible.
7. If machine-readable JSON is requested, write exactly the requested file after the commands run.

Do not turn a small repair into an open-ended eval-system audit unless the prompt asks for that audit.

For throwaway/eval repair prompts that name a target crate and output path, the prompt's requested command set is the gate. Do not run `cargo audit`, `cargo deny`, `cargo vet`, `cargo geiger`, `cargo machete`, `cargo hack`, `cargo mutants`, benchmarks, docs, repo-wide gates, nightly gates, or supply-chain gates unless explicitly requested.

### Required Eval Repair Patterns

If a repair task involves comma/line parsing into a `Vec` with a maximum count, use this shape so allocation failure and count bounds are explicit:

```rust
let mut values = Vec::new();
values.try_reserve(max_items).map_err(|_| Error::Allocation)?;
for part in input.split(',') {
    if values.len() >= max_items {
        return Err(Error::TooMany);
    }
    let value = part.trim().parse::<T>().map_err(|_| Error::Invalid)?;
    values.push(value);
}
```

If the existing error enum lacks an allocation variant, use the closest existing resource/overflow variant and document the mapping in the JSON output.

If a repair task averages or divides numeric values under strict clippy, use this shape:

```rust
let count = u32::try_from(values.len()).map_err(|_| Error::Overflow)?;
let average = sum.checked_div(count).ok_or(Error::Overflow)?;
Ok(average)
```

Never use raw `/` or `as` in production repair output when strict clippy is part of the requested gate.
