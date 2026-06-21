You are running a Holzman Rust SkillOpt repair rollout. Do not use global skills or memory.

Active skill bundle:
- SKILL.md: /tmp/opencode/holzman-skillopt-train/45cf5335eabbbd88/repair_csv_metric_mixed/.skill/holzman-rust/SKILL.md
- references: /tmp/opencode/holzman-skillopt-train/45cf5335eabbbd88/repair_csv_metric_mixed/.skill/holzman-rust/references

Task crate path: /tmp/opencode/holzman-skillopt-train/45cf5335eabbbd88/repair_csv_metric_mixed
Required output path: /tmp/opencode/holzman-skillopt-train/45cf5335eabbbd88/repair_csv_metric_mixed/repair-output.json

Repair exactly the task crate.

Rules:
- Read the active skill bundle and applicable references before editing.
- Repair only the task crate path above.
- Read Cargo.toml, production source, and tests before editing.
- Do not edit tests. Tests are the behavior contract.
- Do not edit Cargo.toml unless compilation is otherwise impossible.
- Make the smallest production-source change that satisfies tests and Holzman + Functional Rust constraints.
- Push logic into pure core and keep I/O/rendering/actions in the shell only when the tests/failure mode require it.
- Remove production unsafe/unwrap/expect/panic/todo/unimplemented/unreachable/assert macros, unchecked indexing, unchecked arithmetic, and lossy as conversions.
- Run cargo fmt after editing, then cargo test.
- Write valid JSON to the required output path after commands run.

Required JSON shape:
{
  "status": "repaired",
  "reference_files_read": ["..."],
  "changed_files": ["src/lib.rs"],
  "commands": [{"command":"cargo test","status":"passed"}],
  "rules_satisfied": ["..."],
  "skipped_gates": [],
  "residual_risk": "..."
}