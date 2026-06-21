# Evaluation And Repair Protocol

This reference makes Holzman Rust behavior measurable in review and repair harnesses. It is additive: if this file conflicts with the canonical Power-of-Ten, unsafe, panic-free, or performance evidence rules, the stricter canonical rule wins.

## Eval Scope Boundary

Eval prompts are scoped contracts. After reading the prompt-named skill bundle and required references, review or repair only the prompt-designated crate, source files, tests, and output file. Do not read or infer work from repo-level `evals/**`, `tasks.json`, `reports/**`, candidate overlays, sibling task crates, or benchmark manifests unless the prompt explicitly names them as the target under review.

When the prompt says to write `review-output.json` or `repair-output.json`, write exactly that file in the prompt-designated working directory or explicit output path. Never write a repo-root output file unless that exact repo-root path is requested. If the designated crate or output path cannot be located, report the missing path as a blocker instead of widening scope.

## Review Output Contract

For review-only tasks, inspect the target files without modifying production source. If the harness asks for `review-output.json`, write this shape:

```json
{
  "status": "reviewed",
  "reference_files_read": ["SKILL.md", "references/nasa-jpl-standards.md"],
  "findings": [
    {
      "severity": "BLOCKER",
      "rule": "zero_forbidden_constructs",
      "file": "src/lib.rs",
      "line": 12,
      "problem": "parse().unwrap() panics on invalid external input",
      "failure_mode": "untrusted input can abort the request instead of returning a typed error",
      "fix": "return a ParseError and handle parse failure with map_err"
    }
  ],
  "missing_evidence": ["no benchmark exists for the stated performance claim"],
  "residual_risk": "static review only; no commands run"
}
```

Findings must be semantic. Do not merely list banned words. A valid finding explains how the construct can fail and what evidence or code shape would close it.

## Repair Output Contract

For repair tasks, preserve tests as the specification. If the harness asks for `repair-output.json`, write this shape after commands run:

```json
{
  "status": "repaired",
  "reference_files_read": ["SKILL.md", "references/nasa-jpl-standards.md"],
  "changed_files": ["src/lib.rs"],
  "commands": [
    {"command": "cargo test", "status": "passed"}
  ],
  "rules_satisfied": ["no unwrap", "checked arithmetic", "typed errors"],
  "skipped_gates": [
    {"gate": "cargo audit", "reason": "not scoped to throwaway eval crate"}
  ],
  "residual_risk": "no benchmark was required for this correctness repair"
}
```

## Repair Ordering

1. Read the skill contract and relevant references.
2. Read `Cargo.toml`, source, and tests before editing.
3. Identify invariants, failure modes, and the public API the tests exercise.
4. Replace panic paths with typed errors or safe `Option`/`Result` handling.
5. Replace unchecked indexing with `get`, iterators, chunks, or prior bound proof.
6. Replace unchecked arithmetic and lossy casts with `checked_*`, `try_from`, `saturating_*`, or documented wrapping semantics.
7. Bound untrusted growth with maximum sizes and `try_reserve` when allocation failure must be graceful.
8. Remove `unsafe` unless the user granted an explicit prior waiver.
9. Run the local commands and record exact outcomes.

## Eval Failure Rules

These fail a review or repair eval even if the final prose sounds plausible:

- Missing required JSON output when explicitly requested.
- Editing tests to make implementation pass.
- Reporting a command as passed without running it.
- Leaving `unsafe`, `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, `unreachable!`, unchecked indexing, unchecked arithmetic, or lossy `as` conversions in production source.
- Claiming performance improvement without benchmark/profiler evidence.
- Treating missing benchmark, profiler, API, or release-provenance evidence as success.
