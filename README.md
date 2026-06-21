# skill-moo

Public SkillOpt example workspace for the Holzman Rust candidate evaluator.

Open `docs/index.html` for the static documentation page with quickstart commands, model configuration, promotion rules, and troubleshooting notes.

## Supported Path

The repository has one supported evaluation route:

- generated corpus: `data/holzman_rust_aggressive`
- generator: `scripts/generate_holzman_rust_dataset.py`
- candidate evaluator: `scripts/run_holzman_candidate_eval.py`
- SkillOpt adapter/grader: `vendor/SkillOpt/skillopt/envs/holzman_rust/`
- active candidate: `candidates/holzman-rust-candidate-v13/SKILL.md`

Historical local training loops, bundle examples, old reports, and generated run summaries are intentionally absent.

## Validate Dataset

```bash
uv run python scripts/generate_holzman_rust_dataset.py --out /tmp/holzman_rust_aggressive_check --seed 42
```

The generated corpus must stay split by `family_id` and `split_family_id` with no cross-split leakage. Expected counts are `train=227`, `val=80`, and `test=80`.

## Run Candidate Eval

```bash
uv run python scripts/run_holzman_candidate_eval.py --out holzman-current --splits val,test --candidate-name holzman-current
```

For MiniMax M3 with OpenCode thinking enabled:

```bash
uv run python scripts/run_holzman_candidate_eval.py \
  --config vendor/SkillOpt/configs/holzman_rust/minimax-v3-thinking.yaml \
  --out holzman-minimax-m3 \
  --splits val,test \
  --candidate-name holzman-minimax-m3
```

Promotion requires full `val,test`, `--kind all`, no `--ids`, `limit: 0`, the checked-in generated split directory, and hard `1.0` on both splits. Targeted reruns may write artifacts, but they are marked `non_promotable` and exit `2`.

## Validate Workspace

```bash
task ci
```

The CI gate compiles the generator/evaluator/rollout modules, runs ruff, runs mypy, regenerates the corpus into `/tmp`, and checks evaluator help output.
