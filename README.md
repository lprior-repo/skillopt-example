# skill-moo

Current Holzman Rust SkillOpt workspace.

There is one supported evaluation path:

- generated corpus: `data/holzman_rust_aggressive`
- generator: `scripts/generate_holzman_rust_dataset.py`
- candidate evaluator: `scripts/run_holzman_candidate_eval.py`
- SkillOpt adapter/grader: `vendor/SkillOpt/skillopt/envs/holzman_rust/`

Legacy offline evaluators, `evals/holzman-rust/tasks.json`, and the old `skillopt_train` package were removed. Do not reintroduce them.

## Skill Bundles

Skills live in `skills/<name>/` and are discovered by the `skillopt_train` harness via `Skill.discover(skills_root)`.

Each skill bundle contains:

- `SKILL.md` — canonical Markdown bundle the harness reads and the mutator appends to
- `rubric.json` — `Rubric.from_mapping` input, with `forbidden_tokens`, `grade_issue_keys`, `grade_returncode_keys`, `success_threshold_hard`, and `max_examples`
- `prompt.md` — mutator prompt template, must include `{skill_md}`, `{previous_addendum}`, `{critique}`, `{max_chars}`, and `{forbidden}` placeholders
- `tasks.jsonl` — fixtures the eval script grades (one JSON object per line)
- `eval.py` — Python entrypoint the harness invokes as `python <skill>/eval.py --tasks ...`
- `config.json` — optional per-skill overrides for `provider_spec`, `eval_model`, `max_steps`, `regression_tolerance`, `opencode_timeout`, `cargo_timeout`

A `references/` directory is allowed for static reference docs the mutator copies into each candidate.

The harness ships two example bundles:

- `skills/holzman-rust/` — NASA/JPL Power-of-Ten Rust doctrine
- `skills/react-typescript/` — TypeScript strict mode plus React 18 hooks

### Adding a New Skill

Each skill lives in `skills/<name>/`. Required files: `SKILL.md`, `rubric.json`, `prompt.md`, `tasks.jsonl`. Plus `eval.py` (or `eval.sh`). Use `uv run skillopt-train run <name>` to evolve.

## Validate Dataset

```bash
.venv/bin/python scripts/generate_holzman_rust_dataset.py --out /tmp/holzman_rust_aggressive_check --seed 42
```

The generated corpus must stay split by `family_id`/`split_family_id` with no cross-split leakage.

## Run Candidate Eval

```bash
.venv/bin/python scripts/run_holzman_candidate_eval.py --out holzman-current --splits val,test --candidate-name holzman-current
```

For MiniMax M3 with OpenCode thinking enabled:

```bash
.venv/bin/python scripts/run_holzman_candidate_eval.py --config vendor/SkillOpt/configs/holzman_rust/minimax-v3-thinking.yaml --out holzman-minimax-m3 --splits val,test --candidate-name holzman-minimax-m3
```

Promotion requires full `val,test`, `--kind all`, no `--ids`, `limit: 0`, and the checked-in generated split directory. Targeted reruns still write artifacts, but are marked `non_promotable` and exit `2`.

## Skill Driven Loop

The `skillopt-train` package ships a registry-based loop driven by `Skill` bundles. Discover and run skills directly without writing a JSON config:

```bash
uv run skillopt-train list --skills-root skills
uv run skillopt-train run holzman-rust --skills-root skills --data-root data/test --steps 1
```

The `list` subcommand prints the discovered skill names. The `run` subcommand accepts the skill name and writes `runs/`, `leaderboard.jsonl`, `budget.json`, and `loop_state.json` under `<data-root>/`.
