# skill-moo

Current Holzman Rust SkillOpt workspace

Open `docs/index.html` for the Stripe-style documentation experience with quickstart commands, model configuration, promotion rules, and troubleshooting notes.

There is one supported evaluation path:

- generated corpus: `data/holzman_rust_aggressive`
- generator: `scripts/generate_holzman_rust_dataset.py`
- candidate evaluator: `scripts/run_holzman_candidate_eval.py`
- SkillOpt adapter/grader: `vendor/SkillOpt/skillopt/envs/holzman_rust/`

Legacy offline evaluators, `evals/holzman-rust/tasks.json`, and the old `skillopt_train` package were removed; do not reintroduce them

## Validate Dataset

```bash
.venv/bin/python scripts/generate_holzman_rust_dataset.py --out /tmp/holzman_rust_aggressive_check --seed 42
```

The generated corpus must stay split by `family_id`/`split_family_id` with no cross-split leakage

## Run Candidate Eval

```bash
.venv/bin/python scripts/run_holzman_candidate_eval.py --out holzman-current --splits val,test --candidate-name holzman-current
```

For MiniMax M3 with OpenCode thinking enabled:

```bash
.venv/bin/python scripts/run_holzman_candidate_eval.py --config vendor/SkillOpt/configs/holzman_rust/minimax-v3-thinking.yaml --out holzman-minimax-m3 --splits val,test --candidate-name holzman-minimax-m3
```

Promotion requires full `val,test`, `--kind all`, no `--ids`, `limit: 0`, and the checked-in generated split directory; targeted reruns still write artifacts, but are marked `non_promotable` and exit `2`

## Skill Bundles

Each skill lives in `skills/<name>/` and is a self-contained bundle the harness discovers, grades, and evolves without writing a JSON config; required files are `SKILL.md`, `rubric.json`, `prompt.md`, and `tasks.jsonl`; the bundle also needs an `eval.py` (or `eval.sh`) entrypoint the harness shells out to; run `uv run skillopt-train run <name>` to evolve a bundle and `uv run skillopt-train list` to discover what is on disk

## Quick Start with a Skill

```bash
uv run skillopt-train list --skills-root skills
uv run skillopt-train run holzman-rust --skills-root skills --data-root data/holzman-rust --steps 4
uv run skillopt-train run react-typescript --skills-root skills --data-root data/react-typescript --steps 4
```

## Adding a New Skill

1. Create `skills/<name>/` with the required files
2. Write `SKILL.md` — the skill bundle being evolved
3. Write `rubric.json` — the forbidden tokens, grade keys, returncode keys
4. Write `prompt.md` — the LLM prompt template with `{placeholders}`
5. Write `tasks.jsonl` — the task fixtures
6. Write `eval.py` (or `eval.sh`) — the eval harness
7. Optionally write `config.json` — default per-skill config
8. Run `uv run skillopt-train run <name> --steps 1` to verify

Each file with a one-line example below

`SKILL.md` — the skill bundle being evolved:

```markdown
# <skill-name> Skill Bundle — summary plus ## Hard Rules, ## Gates, ## No Periods
```

`rubric.json` — the forbidden tokens, grade keys, returncode keys:

```json
{"name": "<skill-name>", "description": "...", "forbidden_tokens": {"token": "forbidden:token"}, "grade_issue_keys": ["forbidden_matches", "execution_errors"], "grade_returncode_keys": ["eval_returncode"], "success_threshold_hard": 1.0, "max_examples": 5}
```

`prompt.md` — the LLM prompt template with `{placeholders}`:

```markdown
You are evolving `{name}`; current SKILL.md={skill_md}; previous addendum={previous_addendum}; critique={critique}; max_chars={max_chars}; forbidden={forbidden}; output JSON {addendum, reasoning}
```

`tasks.jsonl` — the task fixtures:

```jsonl
{"id": "T001", "kind": "review", "code": "source snippet under test", "expected_groups": ["ok"]}
{"id": "T002", "kind": "review", "code": "snippet with forbidden token", "expected_groups": ["forbidden:token"]}
```

`eval.py` — the eval harness:

```python
import argparse, json, sys

def grade(tasks):
    return [{"id": t["id"], "ok": True} for t in tasks]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", required=True)
    p.add_argument("--skill-root", required=True)
    a = p.parse_args()
    with open(a.tasks) as fh:
        tasks = [json.loads(line) for line in fh if line.strip()]
    print(json.dumps(grade(tasks)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

`config.json` — default per-skill config:

```json
{"provider_spec": "mock:dryrun", "eval_model": "", "max_steps": 4, "regression_tolerance": 0.01, "opencode_timeout": 300, "cargo_timeout": 120}
```

## Architecture

```
skills/                     # one directory per skill
├── holzman-rust/
│   ├── SKILL.md
│   ├── rubric.json
│   ├── prompt.md
│   ├── tasks.jsonl
│   ├── eval.py
│   └── config.json
└── react-typescript/
    └── (same structure)
        |
        v
skillopt-train list        # discover
skillopt-train run <name>  # evolve
        |
        v
Skill.discover / Skill.find
        |
        v
SkillDrivenLoop
  ├── Mutator.from_skill  # loads prompt + forbidden tokens from Rubric
  ├── eval_bridge         # shells out to skill's eval.py
  ├── diff_report         # categorizes failures using Rubric
  ├── self_critique       # feeds top failures back to next mutation
  ├── budget              # wall-clock + USD + steps
  ├── leaderboard         # JSONL of every step
  └── providers/          # Anthropic / OpenAI / Opencode / Mock
```

## Built-in Skills

Two skills ship with the repo:

- `holzman-rust` — the canonical Holzman-Rust skill bundle; rubric key fields: `forbidden:unwrap`, `forbidden:expect`, `forbidden:panic`, `forbidden:unsafe`, `forbidden:assert`, `forbidden:as`, `forbidden:indexing`, `forbidden:arithmetic`, `forbidden:string_slice`, `forbidden:get_unwrap`, `forbidden:panic_in_result`, `forbidden:let_underscore`, `forbidden:dbg_macro`; returncode keys: `cargo_fmt_returncode`, `cargo_clippy_returncode`, `cargo_test_returncode`
- `react-typescript` — TypeScript+React hooks rubric example; rubric key fields: `forbidden:any`, `forbidden:unknown`, `forbidden:console`, `forbidden:ts_ignore`, `forbidden:ts_nocheck`, `forbidden:as_unknown_as`; returncode keys: `tsc_returncode`, `eslint_returncode`, `vitest_returncode`
