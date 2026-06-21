## Evaluation And Repair Execution Protocol

For Rust review, repair, and eval-harness tasks, also read `references/evaluation-and-repair-protocol.md` before acting. This addendum strengthens the canonical Holzman Rust doctrine without weakening any existing Power-of-Ten, unsafe, panic-free, benchmark, or verification gate.

### Review Mode

When asked to review Rust code, produce findings that are independently gradable:

- Name the exact rule violated.
- Cite file and line when available.
- State the concrete failure mode, not just the banned token.
- Separate `BLOCKER`, `MAJOR`, and `MINOR` severity.
- Include the smallest compliant fix direction.
- Record missing benchmark, profiler, second-ring, or command evidence as a finding, not as approval.

### Repair Mode

When asked to repair Rust code, inspect the tests and public API before editing, then make the smallest change that satisfies the contract and Holzman constraints. Do not edit tests unless the user explicitly asks for test repair. After editing, run the strongest feasible local gate and record exact commands and outcomes.

### Machine-Readable Eval Output

When an eval prompt asks for JSON, write the requested JSON file and keep it valid. Missing or malformed eval output is a task failure even when prose is correct.

For eval-harness tasks, the prompt-provided target crate and output filename are a hard boundary after reading the skill bundle and required references. Do not discover or aggregate repo-level `evals/**`, `tasks.json`, candidate overlays, or sibling task crates unless the prompt explicitly names them as review targets. If the named crate or output path is unavailable, report that blocker instead of substituting another task list.
