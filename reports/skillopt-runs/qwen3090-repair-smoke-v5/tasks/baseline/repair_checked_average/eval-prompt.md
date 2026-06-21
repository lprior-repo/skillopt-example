You are running a Holzman Rust skill repair evaluation. Do not use global skills or memory.

Skill bundle to evaluate:
- SKILL.md: /tmp/opencode/holzman-skillopt/qwen3090-repair-smoke-v5/tasks/baseline/repair_checked_average/.skill/holzman-rust/SKILL.md
- references: /tmp/opencode/holzman-skillopt/qwen3090-repair-smoke-v5/tasks/baseline/repair_checked_average/.skill/holzman-rust/references

Task: repair exactly one Rust crate.

Task crate path: /tmp/opencode/holzman-skillopt/qwen3090-repair-smoke-v5/tasks/baseline/repair_checked_average
Required output path: /tmp/opencode/holzman-skillopt/qwen3090-repair-smoke-v5/tasks/baseline/repair_checked_average/repair-output.json

Rules:
- Read the skill bundle and applicable references before editing.
- Repair only the task crate path above. Do not inspect parent directories, sibling crates, repo-level eval files, candidates, reports, or task manifests.
- Read Cargo.toml, src/lib.rs, and tests in the task crate path before editing.
- Do not edit tests. Tests are the behavior contract.
- Do not edit Cargo.toml unless the crate cannot compile without a dependency; these eval crates should not need dependency changes.
- Do not use glob. Use direct reads of the files in the task crate path.
- Prefer the smallest production-source change that makes tests pass and satisfies Holzman Rust constraints.
- Remove production unsafe/unwrap/expect/panic/todo/unimplemented/unreachable/assert macros, unchecked indexing, unchecked arithmetic, and lossy as conversions.
- Run cargo test after editing.
- Write valid JSON to the required output path with changed_files, commands, rules_satisfied, skipped_gates, and residual_risk.

Write valid JSON to the required output path with this shape:
{
  "status": "repaired",
  "reference_files_read": ["..."],
  "changed_files": ["src/lib.rs"],
  "commands": [{"command":"cargo test","status":"passed"}],
  "rules_satisfied": ["..."],
  "skipped_gates": [],
  "residual_risk": "..."
}

Final response: one short sentence naming the required output path and whether cargo test passed.