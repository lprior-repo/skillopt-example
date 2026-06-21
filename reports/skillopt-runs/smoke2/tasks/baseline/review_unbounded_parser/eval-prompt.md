You are running a Holzman Rust skill evaluation. Do not use global skills or memory.

Skill bundle to evaluate:
- SKILL.md: /home/lewis/src/skill-moo/reports/skillopt-runs/smoke2/bundles/baseline/holzman-rust/SKILL.md
- references: /home/lewis/src/skill-moo/reports/skillopt-runs/smoke2/bundles/baseline/holzman-rust/references

Task: review the Rust crate in the current working directory for Holzman Rust violations.

Rules:
- Read the skill bundle and applicable references before reviewing.
- Do not edit Cargo.toml, src files, tests, or any production source.
- You may write only review-output.json in the current directory.
- Findings must be concrete, with severity, rule, file, line when possible, problem, failure_mode, and fix.
- Include missing benchmark/profiler/second-ring evidence as findings when relevant.

Write valid JSON to review-output.json with this shape:
{
  "status": "reviewed",
  "reference_files_read": ["..."],
  "findings": [
    {"severity":"BLOCKER","rule":"...","file":"src/lib.rs","line":1,"problem":"...","failure_mode":"...","fix":"..."}
  ],
  "missing_evidence": [],
  "residual_risk": "..."
}

Final response: one short sentence naming review-output.json.