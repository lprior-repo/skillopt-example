# Holzman Rust SkillOpt Analysis

Generated: 2026-06-19T21:39:42.983415+00:00

## Scope

This repository vendors Microsoft SkillOpt and mirrors the rendered SkillOpt guideline page. This report analyzes the local Holzman Rust skill files as a SkillOpt-style skill document: inventory the skill state, score it against a held-out deterministic rubric, then pass or reject through SkillOpt's validation-gate primitive.

No model API calls were made. This is a local static gate and setup report, not a trained SkillOpt `best_skill.md`.

## SkillOpt Inputs

- Docs URL: `https://microsoft.github.io/SkillOpt/docs/guideline.html#what-is`
- Source repo: `/home/lewis/src/skill-moo/vendor/SkillOpt`
- Source commit: `6940e46`
- Source docs files: 18
- Mirrored rendered HTML files: 2
- Rendered guideline: `/home/lewis/src/skill-moo/docs/skillopt-site/microsoft.github.io/SkillOpt/docs/guideline.html`

## Holzman Inputs

| ID                       | Role                                               | Status  | Lines | SHA-256          | Path                                                                                   |
| ------------------------ | -------------------------------------------------- | ------- | ----- | ---------------- | -------------------------------------------------------------------------------------- |
| agents_skill             | canonical doctrine                                 | OK      | 387   | c2f760c9e7bbd6e8 | /home/lewis/.agents/skills/holzman-rust/SKILL.md                                       |
| opencode_skill_bridge    | OpenCode skill bridge                              | OK      | 55    | 8f48756505ff0d91 | /home/lewis/.opencode/skill/holzman-rust/SKILL.md                                      |
| opencode_agent           | OpenCode Holzman Rust agent                        | OK      | 117   | 02c6738ad8f0d80b | /home/lewis/.opencode/agent/holzman-rust.md                                            |
| claude_skill_mirror      | Claude skill mirror referenced by bridge           | MISSING | 0     |                  | /home/lewis/.claude/skills/holzman-rust/SKILL.md                                       |
| ref_nasa_jpl             | Power of Ten and Rust mapping reference            | OK      | 210   | ac0833beab6d19d6 | /home/lewis/.agents/skills/holzman-rust/references/nasa-jpl-standards.md               |
| ref_latency_throughput   | Latency and throughput reference                   | OK      | 377   | 9add10a29ed504df | /home/lewis/.agents/skills/holzman-rust/references/latency-throughput-playbook.md      |
| ref_runtime_architecture | Runtime performance architecture reference         | OK      | 555   | 1dd48f15c3239b63 | /home/lewis/.agents/skills/holzman-rust/references/runtime-performance-architecture.md |
| ref_zero_cost            | Zero-cost abstractions reference                   | OK      | 186   | 24ef8ad9fb511163 | /home/lewis/.agents/skills/holzman-rust/references/zero-cost-abstractions.md           |
| ref_simd                 | SIMD and low-level Rust patterns reference         | OK      | 170   | 40af5fcfa5c0d87b | /home/lewis/.agents/skills/holzman-rust/references/simd-patterns.md                    |
| ref_mechanical_empathy   | Second-ring mechanical empathy toolchain reference | OK      | 81    | 096394a9f002b721 | /home/lewis/.agents/skills/holzman-rust/references/mechanical-empathy-toolchain.md     |

Snapshots and manifest were written under `data/holzman/snapshots`.

## SkillOpt Gate Result

- Hard score: 0.846
- Soft score: 0.885
- Mixed score: 0.865
- Threshold: 0.900
- SkillOpt gate action: `reject`

Interpretation: `accept_new_best` means the local rubric cleared the configured threshold. `reject` means the current local skill mirror should not be treated as a fully clean baseline yet.

## Scorecard

| Gate                                         | Status | Detail                                                                                                                              |
| -------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Required Holzman inputs are readable         | FAIL   | Missing required input(s): /home/lewis/.claude/skills/holzman-rust/SKILL.md                                                         |
| SkillOpt docs and source are local           | PASS   | Rendered docs mirrored: 2 HTML file(s); source docs: 18 file(s); source commit: 6940e46.                                            |
| SkillOpt validation gate imports             | PASS   | SkillOpt evaluation.gate imported.                                                                                                  |
| Machine-readable rule inventory is present   | PASS   | Found 36 rule object(s), 4 gate object(s), and 6 reference object(s).                                                               |
| Power of Ten core coverage                   | PASS   | All expected concept groups found.                                                                                                  |
| Rust forbidden constructs are explicit       | PASS   | All expected concept groups found.                                                                                                  |
| Performance contract coverage                | PASS   | All expected concept groups found.                                                                                                  |
| Prove-slow execute-fast runtime architecture | PASS   | All expected concept groups found.                                                                                                  |
| Mechanical empathy and second-ring evidence  | PASS   | All expected concept groups found.                                                                                                  |
| SIMD safety policy                           | PASS   | All expected concept groups found.                                                                                                  |
| Verification command coverage                | PASS   | All expected concept groups found.                                                                                                  |
| Evidence integrity coverage                  | PASS   | All expected concept groups found.                                                                                                  |
| OpenCode bridge keeps full gate parity       | WARN   | OpenCode bridge/agent omit these stricter gate terms: cargo deny, cargo vet, cargo geiger, cargo machete, cargo hack, cargo mutants |

## Findings

1. **FAIL: Missing required Holzman input: claude_skill_mirror**
Detail: The configured Claude skill mirror referenced by bridge was not readable at /home/lewis/.claude/skills/holzman-rust/SKILL.md.
Recommendation: Create the missing mirror or remove it from the bridge's canonical-source list. Do not treat the mirror as complete until this is fixed.
Evidence:
- `file not found`

2. **WARN: OpenCode bridge/agent gate is weaker than canonical doctrine**
Detail: OpenCode bridge/agent omit these stricter gate terms: cargo deny, cargo vet, cargo geiger, cargo machete, cargo hack, cargo mutants
Recommendation: Either state that the OpenCode gate is only a fast fallback and must defer to the canonical .agents gate, or copy the full supply-chain/mutation gate terms into the bridge/agent.
Evidence:
- `/home/lewis/.opencode/skill/holzman-rust/SKILL.md:40: ## Mandatory Verification Gate`
- `/home/lewis/.opencode/agent/holzman-rust.md:77: - release provenance: `cargo auditable`, `cargo cyclonedx`, SBOM artifact, or documented blocker`
- `/home/lewis/.opencode/agent/holzman-rust.md:91: ## Minimum Fallback Gate`

## Snapshot Manifest Summary

- Manifest entries: 10
- Existing snapshots: 9
- Missing configured inputs: 1

## Rerun

```bash
.venv/bin/python scripts/analyze_holzman.py
```

To refresh Microsoft SkillOpt docs/source first:

```bash
bash scripts/refresh_skillopt_docs.sh
```
