You are running a Holzman Rust skill evaluation. Do not use global skills or memory.

Skill bundle to evaluate:
- SKILL.md: /tmp/opencode/holzman-skillopt/full1/tasks/candidate-v1/review_dense_ir_hot_path/.skill/holzman-rust/SKILL.md
- references: /tmp/opencode/holzman-skillopt/full1/tasks/candidate-v1/review_dense_ir_hot_path/.skill/holzman-rust/references

Task: review exactly one Rust crate for Holzman Rust violations.

Task crate path: /tmp/opencode/holzman-skillopt/full1/tasks/candidate-v1/review_dense_ir_hot_path
Required output path: /tmp/opencode/holzman-skillopt/full1/tasks/candidate-v1/review_dense_ir_hot_path/review-output.json

Rules:
- Read the skill bundle and applicable references before reviewing.
- Review only the task crate path above. Do not inspect parent directories, sibling crates, repo-level eval files, candidates, reports, or task manifests.
- Do not edit Cargo.toml, src files, tests, or any production source.
- Do not run cargo commands for review tasks; this is static review only.
- Do not use glob. Use direct reads of the files in the task crate path.
- You may write only the required output path above.
- Findings must be concrete, with severity, rule, file, line when possible, problem, failure_mode, and fix.
- Include missing benchmark/profiler/second-ring evidence as findings when relevant.

Write valid JSON to the required output path with this shape:
{
  "status": "reviewed",
  "reference_files_read": ["..."],
  "findings": [
    {"severity":"BLOCKER","rule":"...","file":"src/lib.rs","line":1,"problem":"...","failure_mode":"...","fix":"..."}
  ],
  "missing_evidence": [],
  "residual_risk": "..."
}

Final response: one short sentence naming the required output path.