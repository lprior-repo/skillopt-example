You are evolving a TypeScript skill called `react-typescript`

Existing skill bundle (truncated):
```
{skill_md}
```

Previous candidate addendum (may be empty on first step):
```
{previous_addendum}
```

Self-critique from the previous step's grading report:
{critique}

Rules:
- Output a single JSON object: {{"addendum": "...", "reasoning": "..."}}
- The `addendum` is appended to the canonical SKILL.md
- It must be Markdown only
- Maximum length: {max_chars} characters
- Do NOT introduce these forbidden tokens in the addendum: {forbidden}
- Address the top failure modes listed in the self-critique
- Prefer concrete, testable rules over prose
- Cite specific gates (tsc --noEmit, eslint, vitest)
- If the critique is empty, propose the smallest change that strengthens the
  strongest existing rule in the skill bundle

Output ONLY the JSON object
No preamble, no explanation, no markdown headings