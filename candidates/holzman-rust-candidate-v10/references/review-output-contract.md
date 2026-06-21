# Review Output Contract

Use when a prompt requires machine-readable review output.

```json
{
  "status": "reviewed",
  "reference_files_read": ["SKILL.md"],
  "findings": [
    {
      "severity": "BLOCKER",
      "rule": "zero_forbidden_constructs",
      "file": "src/lib.rs",
      "line": 12,
      "construct": "parse().unwrap()",
      "problem": "invalid external input panics",
      "failure_mode": "untrusted input aborts the request instead of returning a typed error",
      "fix": "return a typed ParseError and handle parse failure with map_err"
    }
  ],
  "missing_evidence": ["no benchmark exists for the stated performance claim"],
  "residual_risk": "static review only; no commands run"
}
```

Findings must be semantic. Do not merely list banned words. Include concrete failure modes and smallest safe fixes.
