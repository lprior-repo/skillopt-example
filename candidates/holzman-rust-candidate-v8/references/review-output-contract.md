# Review Output Contract

Use this reference when a prompt asks for machine-readable review output.

## JSON Shape

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
      "fix": "return a ParseError and handle parse failure with map_err"
    }
  ],
  "missing_evidence": ["no benchmark exists for the stated performance claim"],
  "residual_risk": "static review only; no commands run"
}
```

## Rules

- Findings must be semantic and tied to actual code.
- Do not merely list banned words.
- Include concrete failure modes and smallest safe fixes.
- Include missing evidence when the code or comments make safety, performance, compatibility, or proof claims.
- Write the exact requested output path and validate JSON parseability when tools allow it.
