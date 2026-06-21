# Contributing

Holzman Rust SkillOpt workflow for evolving per-domain review bundles

Welcome to the `skill-moo` contribution guide This file documents how to evolve skill bundles, add CLI subcommands, and author evaluators Every section follows the period-free prose convention enforced by the Holzman Rust doctrine and verified by a regression test

## Architecture Overview

The repository is a single-process SkillOpt harness that evolves per-domain review bundles through a registry-driven loop Skills live as directories under `skills/`. The loop reads them, mutates them, evaluates them, and persists artifacts under `data/` plus `runs/`.

### Data Flow

```
skills/<name>/
   SKILL.md           canonical bundle the mutator appends to
   rubric.json        forbidden tokens + grading keys + thresholds
   prompt.md          mutator template with placeholders
   tasks.jsonl        fixtures the eval script grades
   eval.py            harness entrypoint per candidate
   config.json        optional per-skill loop overrides
   references/        optional static docs copied into each overlay
```

The harness exposes the bundles through `Skill.discover`, `Skill.find`, `Mutator.from_skill`, and `SkillDrivenLoop`. Each function has a single responsibility and is composed by the CLI in `scripts/skillopt_train/__main__.py`.

### Discovery And Validation

- `Skill.discover(skills_root)` walks `skills_root` and returns every directory with all required files
- `Skill.find(skills_root, name)` validates the name against `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` then loads one bundle
- Both raise `ConfigError` with stable `code` strings (`skill_incomplete`, `skill_name_invalid`, `skill_not_found`)
- Names starting with `.` are skipped silently during discovery
- Directories missing required files are also skipped silently during discovery but reported by `Skill.find`

### Mutator Wiring

- `Mutator.from_skill(skill)` reads `prompt.md` plus the parsed `Rubric` and constructs the proposer
- The proposer fills the placeholders `{skill_md}`, `{previous_addendum}`, `{critique}`, `{max_chars}`, `{forbidden}`
- Forbidden tokens from `rubric.json` are joined by `, ` and interpolated into the prompt verbatim
- The mutator returns a JSON object with `addendum` and `reasoning` keys
- The harness parses the response with `json.loads` and rejects anything that is not a dict

### Loop Driver

- `SkillDrivenLoop(skill, config)` orchestrates the propose-grade-gate-persist cycle
- Each step writes `runs/<run_id>/summary.json` plus updates `data/<root>/leaderboard.jsonl` and `loop_state.json`
- The driver accepts `regression_tolerance` and `success_threshold_hard` from the rubric plus config
- The driver writes `data/<root>/budget.json` so quota consumption is auditable

### Loop Sequence

1. `SkillDrivenLoop` reads the bundle `prompt.md` and the current `SKILL.md`
2. `Mutator.from_skill(skill)` proposes `{"addendum": ..., "reasoning": ...}` per the placeholders
3. The harness stages a candidate overlay by appending the addendum to a copy of `SKILL.md`
4. `eval.py` runs against the overlay and writes `runs/<run_id>/summary.json`
5. The leaderboard comparator gates against `success_threshold_hard` and `regression_tolerance`
6. The accepted addendum is appended to `SKILL.md` and `loop_state.json` advances
7. The next iteration starts from the accepted `SKILL.md` so each step builds on the last

### Component Responsibilities

| Component | Responsibility |
| --- | --- |
| `Skill.discover` | Walk a skills root and return every valid bundle |
| `Skill.find` | Validate one name and load one bundle |
| `Rubric.from_path` | Parse `rubric.json` into a typed dataclass |
| `Mutator.from_skill` | Bind a `prompt.md` plus a `Rubric` into a proposer |
| `SkillDrivenLoop` | Drive the propose-eval-gate-persist cycle |
| `eval.py` | Black-box evaluator per bundle |

## Development Setup

### Prerequisites

- Python 3.11 or newer
- `uv` for dependency management
- `git` for source control
- Optional: `cargo` plus `rustup` for Rust-specific bundles
- Optional: `node` plus `pnpm` for TypeScript-specific bundles

### Clone And Install

```bash
git clone <repo-url>
cd skill-moo
uv sync
```

The `uv sync` step resolves the locked toolchain, installs the `skillopt-train` package, and provisions `.venv/`. The console script `skillopt-train` is registered on `$PATH` inside the venv

### Verify The Toolchain

```bash
uv run python -V
uv run skillopt-train --help
uv run pytest --collect-only
```

All three commands must succeed before you open a pull request The first prints the interpreter version The second prints the registered subcommands The third enumerates the test suite

### Repository Layout

```
skill-moo/
   README.md
   CONTRIBUTING.md
   pyproject.toml
   uv.lock
   scripts/
      skillopt_train/      the harness package
      generate_holzman_rust_dataset.py
      run_holzman_candidate_eval.py
   skills/
      holzman-rust/        example Rust bundle
      react-typescript/    example TS+React bundle
   data/                   generated corpora + run artifacts
   runs/                   per-step eval outputs
   candidates/             promoted bundles
   vendor/SkillOpt/        upstream SkillOpt checkout
   tests/                  pytest suite
   docs/                   rendered guides
   .benchmarks/            performance traces
   reports/                audit reports
```

### Environment Variables

- `SKILLOPT_PROVIDER` — provider spec passed to the mutator when `--provider-spec` is absent
- `SKILLOPT_DATA_ROOT` — default data root for `skillopt-train run`
- `SKILLOPT_OPENCODE_TIMEOUT` — global fallback for `opencode_timeout`
- `SKILLOPT_CARGO_TIMEOUT` — global fallback for `cargo_timeout`

## Running Tests

### Unit Tests

```bash
uv run pytest tests/unit -q
```

Unit tests cover pure functions in `scripts/skillopt_train/` such as `Rubric.from_mapping`, `Mutator.from_skill`, and the gate comparator

### Integration Tests

```bash
uv run pytest tests/integration -q
```

Integration tests spawn the harness in a temp directory and assert on `runs/`, `leaderboard.jsonl`, and `loop_state.json` artifacts

### Skill Bundle Smoke Tests

```bash
uv run pytest tests/skills -q
```

The smoke tests invoke `Skill.discover` and confirm every bundle has the required files plus a parseable rubric They also assert that no addendum leaked a forbidden token

### Manual Smoke Run

```bash
uv run skillopt-train run holzman-rust --skills-root skills --data-root data/test --steps 1
```

A manual run writes `data/test/runs/<run_id>/summary.json`, `data/test/leaderboard.jsonl`, and `data/test/loop_state.json`. Inspect each file to confirm the loop behaved as expected

## Lint And Typecheck

### Ruff

```bash
uv run ruff check .
uv run ruff format --check .
```

Ruff enforces import order, unused-symbol detection, and the project style guide The `--check` flag reports formatting drift without rewriting files

### Mypy

```bash
uv run mypy scripts/skillopt_train
```

Mypy enforces the strict-optional policy plus PEP 695 type aliases used throughout the harness The config lives in `pyproject.toml`.

### Combined Gate

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy scripts/skillopt_train
```

CI runs this combined gate on every push Pull requests that fail any step are blocked from merge

## Adding a New CLI Subcommand

### Step 1: Pick The Layer

Decide whether the subcommand belongs in the `skillopt_train` package or in the standalone scripts directory Most contributors will add to the package so the subcommand becomes part of the `skillopt-train` console script Use the standalone scripts directory only for one-off operators that ship with no tests

### Step 2: Wire Argparse

Add an argparse parser to the relevant module Follow the period-free rule in every help string and error message Reject `--flag` values that fail validation up front so the rest of the function can stay pure

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillopt-train <subcommand>")
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--steps", type=int, default=1)
    return parser
```

### Step 3: Register In `__main__`

Import the new subcommand and route it from `scripts/skillopt_train/__main__.py`. Add a docstring describing its purpose plus a one-line usage example The route must live behind a clear `match` arm so future subcommands slot in cleanly

### Step 4: Add Tests

Cover the happy path plus every error path Use `pytest` fixtures from `tests/conftest.py` for the harness scaffolding The fixtures provision a temp `skills/` tree plus a temp `data/` root so tests stay hermetic

### Step 5: Document In README

Add a one-line entry plus a minimal example under `README.md`. Cross-link to the relevant section of this guide Update `docs/skillopt-site/` if the subcommand deserves a rendered page

## Adding a New Skill

Each skill is a directory under `skills/<name>/`. The harness discovers it via `Skill.discover` and validates it via `Skill.find`. Every required file is required; missing files raise `ConfigError` with `code="skill_incomplete"`. The bundle is the unit of evolution: one directory per language, framework, or review doctrine

### Step 1: Create The Skill Directory

```bash
mkdir -p skills/my-skill
cd skills/my-skill
```

The skill name must match `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` (validated by `Skill.find`) Names starting with `.` are skipped during discovery Reserved names include `__pycache__`, `__init__`, and any name containing whitespace

#### Recommended Layout

```
skills/my-skill/
   SKILL.md
   rubric.json
   prompt.md
   tasks.jsonl
   eval.py
   config.json
   references/
      style-guide.md
      api-notes.md
```

#### Naming Tips

- Use lowercase plus hyphens for multi-word names (`react-typescript`, `python-typing`)
- Use a single token for one-word names (`go`, `rust`, `sql`)
- Avoid vendor names unless the bundle is vendor-specific (`aws-cdk`, `gcp-iam`)

### Step 2: Write `SKILL.md`

The canonical bundle the harness reads and the mutator appends to Size between 1 KB and 10 KB Write clear rules and cite specific gates Every bullet should be testable by either a static check or a runtime assertion

#### Writing Rules

- One rule per bullet
- Use backticks for code tokens
- Cite the gate that enforces each rule
- Avoid prose periods at the end of bullets
- Prefer negative phrasing (`Never use X`) over positive phrasing (`Avoid X`) when possible

#### Example

```markdown
# My-Skill Skill Bundle

Domain-specific review rules for the my-skill bundle

## Hard Rules

- Never use `<token>`; use `<typed alternative>` instead
- Never call `<risky API>` without a typed guard
- Every public function carries a doc comment with an example

## Required Coverage Gates

Every change must pass:

- `make lint`
- `make test`
- `make audit`

## Module Layout

- One type per file when the type exceeds 80 lines
- Group related small types in one module under a `mod.rs`
```

#### Size Constraint

The harness enforces a 1-10 KB size window on `SKILL.md`. Smaller bundles are rejected as too sparse; larger bundles are rejected as too noisy The check runs on the canonical text plus the cumulative addenda so growth is bounded over the loop lifetime

### Step 3: Write `rubric.json`

The Rubric schema The harness parses this file with `Rubric.from_path` and exposes it via `Skill.rubric`. Every field is optional except `name`; missing fields fall back to safe defaults

#### Schema

```json
{
  "name": "my-skill",
  "description": "what this skill covers",
  "forbidden_tokens": {
    "token_name": "forbidden:bucket_name"
  },
  "grade_issue_keys": ["json_errors", "mutation_errors"],
  "grade_returncode_keys": ["my_gate_returncode"],
  "success_threshold_hard": 1.0,
  "max_examples": 5
}
```

#### Field Reference

- `name` — must equal the directory name; used in leaderboard entries
- `description` — one-line summary shown in `list` output
- `forbidden_tokens` — maps source tokens to bucket names the grader counts
- `grade_issue_keys` — keys the harness reads from the eval summary
- `grade_returncode_keys` — keys the harness reads from gate returncodes
- `success_threshold_hard` — float in `[0, 1]`; gate rejects below this
- `max_examples` — int; how many tasks the eval should run per step

#### Forbidden Token Naming

Bucket names follow the convention `forbidden:<category>`. Categories group related tokens so the grader can roll up violations into a single counter Common categories include `unwrap`, `panic`, `dbg_macro`, `console`, `any`, and `as`.

| Token | Bucket | Rationale |
| --- | --- | --- |
| `unwrap` | `forbidden:unwrap` | Panics on `None` or `Err` |
| `expect` | `forbidden:expect` | Same risk class as `unwrap` |
| `panic!` | `forbidden:panic` | Unrecoverable failure |
| `dbg!` | `forbidden:dbg_macro` | Leaks debug output |
| `console.log` | `forbidden:console` | Bypasses typed logger |

### Step 4: Write `prompt.md`

The LLM prompt template The harness fills these placeholders per step:

- `{skill_md}` — the canonical SKILL.md content
- `{previous_addendum}` — last step's addendum (may be empty)
- `{critique}` — the self-critique from the last step
- `{max_chars}` — maximum addendum length
- `{forbidden}` — comma-separated forbidden tokens

#### Template

```markdown
You are evolving a <domain> skill called `<name>`

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
- Cite specific gates (`<gate a>`, `<gate b>`)
- If the critique is empty, propose the smallest change that strengthens the
  strongest existing rule in the skill bundle

Output ONLY the JSON object
No preamble, no explanation, no markdown headings
```

#### Validation

The harness raises `ConfigError` with `code="prompt_missing_placeholder"` when a required placeholder is absent Extra placeholders raise `code="prompt_unknown_placeholder"`. Both checks run on bundle load so authors see errors immediately

#### Prompting Tips

- Quote each gate verbatim so the LLM cannot paraphrase them
- Pin the output format to a single JSON object so the parser stays simple
- Include a fallback instruction for the empty-critique case so step 0 is well-defined
- Cap `max_chars` at 2000 by default; longer addenda dilute the bundle

### Step 5: Write `tasks.jsonl`

One JSON object per line The harness reads this with `json.loads` per line and feeds it to `eval.py`. Blank lines and comment lines are skipped so authors can add `# TODO` markers freely

#### Schema

```json
{"id": "T001", "kind": "review", "code": "fn foo() {}", "expected_groups": ["ok"]}
```

#### Field Reference

- `id` — stable string used by `--task-id` filters
- `kind` — string the eval interprets (for example `review`, `mutation`, `execution`)
- `code` — the source snippet under test
- `expected_groups` — list of bucket names the task should land in

#### Conventions

- One task per line; no trailing commas
- Stable IDs (`T001`, `T002`, ...) so reruns are diffable
- Include both positive and negative cases
- Mix `kind` values so the eval exercises every path

#### Coverage Targets

Aim for at least one task per `forbidden_token` bucket so the grader can detect regressions Add a few `ok` tasks as the negative-control baseline The harness caps tasks at `max_examples` per step

### Step 6: Write `eval.py` (or `eval.sh`)

The eval harness Receives the candidate overlay and tasks; produces a `summary.json` in the run root The harness treats the script as a black box that returns exit code 0 on success plus a parseable `summary.json`.

#### Required CLI

```bash
python skills/my-skill/eval.py \
   --tasks /path/to/tasks.jsonl \
   --candidate-name my-skill \
   --candidate-overlay-dir /path/to/overlay \
   --run-id <uuid> \
   --sandbox-root /path/to/sandbox \
   --timeout 300 \
   --kind all
```

#### Output Schema

The script must write `runs/<run_id>/summary.json` with the shape:

```json
{
  "aggregates": [
    {
      "bundle": "<candidate_name>",
      "hard": 0.85,
      "soft": 0.5,
      "mixed": 0.65,
      "passed_tasks": 3,
      "task_count": 4
    }
  ],
  "gate": {"action": "kept"}
}
```

#### Minimal Example

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
   parser = argparse.ArgumentParser(prog="my-skill eval")
   parser.add_argument("--tasks", required=True)
   parser.add_argument("--candidate-name", required=True)
   parser.add_argument("--candidate-overlay-dir", required=True)
   parser.add_argument("--run-id", required=True)
   parser.add_argument("--sandbox-root", required=True)
   parser.add_argument("--timeout", type=int, default=300)
   args = parser.parse_args(argv)

   tasks_path = Path(args.tasks)
   tasks = [
      json.loads(line)
      for line in tasks_path.read_text().splitlines()
      if line.strip()
   ]

   passed = sum(
      1 for t in tasks if set(t.get("expected_groups", [])) <= {"ok"}
   )

   run_root = Path(args.sandbox_root).parent / "runs" / str(args.run_id)
   run_root.mkdir(parents=True, exist_ok=True)

   summary = {
      "aggregates": [
         {
            "bundle": args.candidate_name,
            "hard": passed / max(len(tasks), 1),
            "soft": passed / max(len(tasks), 1),
            "mixed": passed / max(len(tasks), 1),
            "passed_tasks": passed,
            "task_count": len(tasks),
         }
      ],
      "gate": {"action": "kept"},
   }

   (run_root / "summary.json").write_text(
      json.dumps(summary, indent=2, sort_keys=True) + "\n"
   )
   return 0


if __name__ == "__main__":
   raise SystemExit(main(sys.argv[1:]))
```

A simple eval can read `tasks.jsonl`, score each task, and write the summary

#### Common Patterns

- Forbid one forbidden token per task so failures are attributable
- Run gates in parallel with `concurrent.futures` when the bundle is large
- Capture stderr per task and stash it under `runs/<run_id>/logs/`
- Always exit 0 on a successful summary write, even when tasks failed

### Step 7: Optionally Write `config.json`

Default per-skill loop config The harness merges this with the global config plus CLI flags Per-skill values win over global values; CLI flags win over per-skill values

#### Schema

```json
{
  "provider_spec": "opencode:claude-sonnet",
  "eval_model": "claude-sonnet-4-5",
  "max_steps": 8,
  "regression_tolerance": 0.01,
  "opencode_timeout": 600,
  "cargo_timeout": 300
}
```

#### Field Reference

- `provider_spec` — `<provider>:<model>` string passed to the mutator
- `eval_model` — model id used by the eval driver (may be empty for `mock:dryrun`)
- `max_steps` — int; max iterations before the loop aborts
- `regression_tolerance` — float; how much soft score can drop before gate rejects
- `opencode_timeout` — seconds; per-step wall clock for the mutator
- `cargo_timeout` — seconds; per-step wall clock for cargo gates

#### Merging Rules

The merge order is global config then per-skill config then CLI flags Numeric fields use max-of String fields use last-wins Unknown keys are ignored with a warning logged to `budget.json`.

### Step 8: Test The Skill

```bash
uv run skillopt-train list --skills-root skills
uv run skillopt-train run my-skill --skills-root skills --data-root data/test --steps 1
```

Verify the leaderboard shows your skill and the eval produces a `summary.json`.

#### Expected Output

```
skills/my-skill
```

#### Expected Artifacts

- `data/test/runs/<run_id>/summary.json`
- `data/test/leaderboard.jsonl`
- `data/test/loop_state.json`
- `data/test/budget.json`

If any artifact is missing, inspect `data/test/budget.json` for quota consumption and consult the Troubleshooting section below

#### Iterating

Run the harness with `--steps 1` until the candidate passes the gate Then bump to `--steps 4` and confirm the bundle still evolves cleanly Promote the candidate by copying it under `candidates/` once the leaderboard stabilizes

## Skill Bundle Schema Reference

Quick reference for every file in a skill bundle Each entry lists whether the file is required, its size constraint, and the harness entrypoint that reads it

### `SKILL.md`

- Required
- Size 1-10 KB of Markdown
- Read by `Skill.skill_md` and `Mutator.from_skill`
- Append target for accepted addenda

### `rubric.json`

- Required
- Parsed by `Rubric.from_path`
- See Step 3 for the full schema

### `prompt.md`

- Required
- Must have `{skill_md}` `{previous_addendum}` `{critique}` `{max_chars}` `{forbidden}` placeholders
- Read by `Skill.load_prompt`
- Validated by the harness on bundle load

### `tasks.jsonl`

- Required
- One task per line
- Read by the eval harness
- Stable IDs preferred

### `eval.py`

- Required (or `eval.sh`)
- Must write `runs/<run_id>/summary.json`
- Invoked by the harness with the standard CLI shown in Step 6

### `config.json`

- Optional
- Default per-skill loop config
- Merged on top of the global config

### `references/`

- Optional
- Static reference docs the mutator copies to each candidate overlay
- Treated as read-only by the harness

## Loop Internals

This section documents the inner workings of `SkillDrivenLoop`. Most contributors can skip it, but skill authors writing custom evals should understand the loop

### `SkillDrivenLoop` Phases

Each loop step executes four phases:

- `propose` — call `Mutator.from_skill(skill).propose()` to obtain the JSON addendum
- `stage` — write a candidate overlay by appending the addendum to a copy of `SKILL.md`
- `eval` — invoke `eval.py` with the standard CLI and parse `summary.json`
- `gate` — compare against `success_threshold_hard` and `regression_tolerance`

### `Mutator.from_skill`

Reads `prompt.md` plus the parsed `Rubric` and constructs the proposer The proposer fills placeholders verbatim Forbidden tokens are joined by `, ` and interpolated into the prompt

### Prompt Placeholders

The harness supports exactly five placeholders:

- `{skill_md}` — replaced with the canonical bundle text
- `{previous_addendum}` — replaced with the last accepted addendum (empty on step 0)
- `{critique}` — replaced with the self-critique from the last grading report
- `{max_chars}` — replaced with the integer character budget
- `{forbidden}` — replaced with the comma-separated token list

Any other placeholder causes `ConfigError` with `code="prompt_unknown_placeholder"`.

### Eval Output Schema

The eval must write `summary.json` with two top-level keys:

- `aggregates` — list of per-candidate rollups
- `gate` — decision object with `action` in `{"kept", "rejected", "aborted"}`

Each aggregate must include `bundle`, `hard`, `soft`, `mixed`, `passed_tasks`, and `task_count`.

### Gate Logic

The gate computes three scores per candidate:

- `hard` — fraction of tasks with `expected_groups <= {"ok"}`
- `soft` — fraction of tasks with at least one matching bucket
- `mixed` — average of `hard` and `soft`

A candidate is kept when `hard >= success_threshold_hard` AND `mixed >= previous_mixed - regression_tolerance`.

### Persistence Layout

After each step the loop writes:

- `runs/<run_id>/summary.json` — per-step eval result
- `data/<root>/leaderboard.jsonl` — append-only candidate log
- `data/<root>/loop_state.json` — current bundle + step counter + budget
- `data/<root>/budget.json` — token and wall-clock consumption

## Authoring Evaluators

This section is for contributors writing custom `eval.py` scripts The harness treats the script as a black box that returns exit code 0 on success plus a parseable `summary.json`.

### Inputs

- `--tasks` — absolute path to `tasks.jsonl`
- `--candidate-name` — string identifying the candidate (for example `holzman-rust-cand-3`)
- `--candidate-overlay-dir` — absolute path to the staged overlay
- `--run-id` — UUID the harness uses for the run directory
- `--sandbox-root` — absolute path the eval may use as a scratch root
- `--timeout` — seconds; soft wall clock for the eval
- `--cargo-timeout` — seconds; soft wall clock for cargo commands (Rust bundles)
- `--kind` — `all` | `review` | `mutation` | `execution`
- `--model` — model id for grading; empty if the eval does not need it
- `--limit` — int; max tasks to grade (0 = no limit)
- `--task-id` — repeatable; specific task IDs to grade

### Outputs

- `runs/<run_id>/summary.json` — must be parseable JSON with the schema in Step 6
- Exit code 0 — success
- Exit code non-zero — failure; the harness treats the step as aborted

### Scoring Conventions

- `hard` — strict pass; `expected_groups` is a subset of `{"ok"}`
- `soft` — partial credit; `expected_groups` intersects with the candidate's matching buckets
- `mixed` — average of `hard` and `soft`

### Sandbox Conventions

- Write only inside `sandbox_root` and `runs/<run_id>/`
- Do not modify files outside the overlay
- Do not call network services unless the rubric explicitly allows it
- Clean up temp directories on every exit path

### Error Handling

- Catch every exception and translate it into a non-zero exit code
- Write a failure record to `runs/<run_id>/error.json` before exiting
- Include the original traceback plus the failing task ID
- Never silently swallow an exception

## Provider Configuration

### `provider_spec`

String of the form `<provider>:<model>`. The harness dispatches to the matching provider module under `scripts/skillopt_train/providers/`. Supported providers include `opencode`, `mock`, and `anthropic`.

### `eval_model`

Optional model id used by the eval driver Empty string means the eval runs without an LLM (for example `mock:dryrun`) When set, the eval may invoke the model to grade ambiguous tasks

### Timeouts

- `opencode_timeout` — seconds; per-step mutator wall clock
- `cargo_timeout` — seconds; per-step cargo wall clock
- Global `timeout` — fallback for any sub-step without an explicit budget

## Troubleshooting

### Skill Not Discovered

- Check the directory name matches `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`
- Check the directory does not start with `.`
- Confirm all required files exist
- Run `uv run skillopt-train list --skills-root skills` to inspect

### Skill Name Rejected

- `Skill.find` validates the name regex before reading files
- Replace any character outside `[A-Za-z0-9_.-]` in the directory name
- Confirm the name length is between 1 and 64 characters

### Rubric Parse Error

- Run `uv run python -c "import json; json.load(open('skills/<name>/rubric.json'))"` to validate
- Confirm the JSON root is an object
- Confirm `forbidden_tokens` is a map of string to string

### Eval Timeout

- Raise `--timeout` in the loop config
- Split long tasks into smaller fixtures
- Profile the eval script with `uv run python -c "import cProfile; ..."`

### Forbidden Token Leakage

- The mutator interpolates forbidden tokens into `{forbidden}`
- The grader counts matches against `forbidden_tokens`
- Confirm the addendum does not introduce new tokens that match the bucket map
- Re-run with `--steps 1` and inspect `runs/<run_id>/summary.json`

### Mutator Returns Empty Addendum

- Confirm the LLM responded with valid JSON
- Increase `max_chars` so the model has room to write
- Tighten the prompt so the model cannot dodge with an empty string
- Re-run with `mock:dryrun` to isolate provider issues from prompt issues

### Leaderboard Drift

- Compare `leaderboard.jsonl` entries with `git log -p candidates/<name>/`
- Confirm `success_threshold_hard` matches the rubric value
- Confirm `regression_tolerance` is not too tight for the bundle

### Diff Report Mismatch

- Re-run `scripts/run_holzman_candidate_eval.py` to refresh the diff
- Confirm the candidate name matches the directory under `candidates/`
- Confirm the overlay directory was not deleted between steps

## Conventions

### Period-Free Prose

Every prose sentence in source code, error messages, and CLI descriptions ends without a period The harness enforces this rule via a regression test that scans for `[letter].\s` patterns The test is fast and runs on every push

### Functional Core Imperative Shell

The harness separates pure logic (parsing, scoring, gating) from side effects (file I/O, network calls) Keep new code on the pure side when possible Side effects belong in `eval.py` or in provider modules under `scripts/skillopt_train/providers/`.

### No Unwrap In Production Code

Production paths must not call `unwrap`, `expect`, `panic!`, `todo!`, or `unimplemented!`. Helper functions return `Result<T, E>` instead The rule is enforced by a clippy lint at `scripts/skillopt_train/`.

### Doc Comments

Every public function, struct, enum, trait, and module carries a doc comment Examples in doc comments must compile The `missing_docs` lint is deny-by-default Doc comments end without a period for short summaries and with a period only for full multi-sentence blocks where the period rule is not in force

## Release Process

### Versioning

The project follows Semantic Versioning Breaking changes bump the major version New features bump the minor version Bug fixes bump the patch version The version lives in `pyproject.toml` plus `scripts/skillopt_train/__init__.py`.

### Tagging

```bash
git tag -s vX.Y.Z -m "release vX.Y.Z"
git push origin vX.Y.Z
```

Tags are signed with the maintainer's GPG key CI builds the wheel plus the sdist on every tag push and uploads them to the internal index

### Publishing

```bash
uv build
uv publish --index internal
```

The `internal` index is configured in `pyproject.toml`. The package is consumed by downstream rigs that pin a specific minor version

## FAQ

### How Do I Add A Skill For A New Language

Pick a name that matches the language plus a distinguishing suffix if needed (`python-typing`, `go-context`, `rust-async`) Mirror the layout from `skills/holzman-rust/`. Fill in every required file Test with `uv run skillopt-train run <name> --steps 1`.

### How Do I Add A New Gate

Add a new entry to `rubric.json` under `grade_returncode_keys`. Update `eval.py` to populate the corresponding returncode in `summary.json`. Confirm the gate runs in CI before opening a pull request

### How Do I Run Only One Step

Pass `--steps 1` to `skillopt-train run`. The harness exits after the first iteration regardless of the gate outcome Use this mode when iterating on a prompt or rubric

### How Do I Promote A Candidate

Copy the candidate overlay under `candidates/<name>/` once the leaderboard stabilizes Update `README.md` with a one-line entry Tag a release so downstream consumers can pin the new bundle

## Glossary

### Bundle

A skill directory under `skills/<name>/`. The unit of evolution One bundle per language, framework, or review doctrine

### Addendum

A Markdown snippet proposed by the mutator and appended to the canonical `SKILL.md`. Addenda are bounded by `max_chars` per step

### Overlay

A staged copy of a bundle plus the proposed addendum The eval runs against the overlay so the canonical bundle stays clean until the gate accepts

### Gate

The comparator that accepts or rejects a candidate based on `success_threshold_hard` and `regression_tolerance`. Rejections still write artifacts but do not advance `loop_state.json`.

### Bucket

A short string (`forbidden:<category>`) that groups related violations The grader counts matches per bucket so a single rule failure does not drown out the rest

### Loop State

The JSON object at `data/<root>/loop_state.json` that records the current bundle plus the step counter plus the budget The harness rewrites this file on every accepted step

### Run ID

A UUID the harness generates per step Used as the directory name under `runs/` and as the suffix for `summary.json` plus `error.json`.