# Review Output Contract

Use this reference only when a prompt asks for machine-readable review output or when the task is explicitly a review evaluation. It is not required for ordinary implementation or repair work.

When asked for JSON review output, write this shape to the exact requested path:

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
