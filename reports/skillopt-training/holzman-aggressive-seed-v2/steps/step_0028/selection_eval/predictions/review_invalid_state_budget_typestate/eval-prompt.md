You are running a Holzman Rust SkillOpt rollout. Do not use global skills or memory.

Active skill bundle:
- SKILL.md: /tmp/opencode/holzman-skillopt-train/13b0e54de29d6b23/review_invalid_state_budget_typestate/.skill/holzman-rust/SKILL.md
- references: /tmp/opencode/holzman-skillopt-train/13b0e54de29d6b23/review_invalid_state_budget_typestate/.skill/holzman-rust/references

Task crate path: /tmp/opencode/holzman-skillopt-train/13b0e54de29d6b23/review_invalid_state_budget_typestate
Required output path: /tmp/opencode/holzman-skillopt-train/13b0e54de29d6b23/review_invalid_state_budget_typestate/review-output.json

Review exactly the task crate for Holzman + Functional Rust violations.

Rules:
- Read the active skill bundle and applicable references before reviewing.
- Review only the task crate path above.
- Do not inspect parent directories, sibling tasks, eval manifests, candidates, or reports.
- Do not edit Cargo.toml, source, tests, or production files.
- Do not run cargo commands for review tasks.
- You may write only the required output path.
- Findings must include severity, rule, file, line, problem, failure_mode, and fix.
- Include missing benchmark/profiler/allocation/second-ring/command evidence as findings when relevant.

Write valid JSON to the required output path:
{
  "status": "reviewed",
  "reference_files_read": ["..."],
  "findings": [{"severity":"BLOCKER","rule":"...","file":"src/lib.rs","line":1,"problem":"...","failure_mode":"...","fix":"..."}],
  "missing_evidence": [],
  "residual_risk": "..."
}