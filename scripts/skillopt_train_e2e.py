from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skillopt_train.budget import Budget, BudgetConfig
from skillopt_train.leaderboard import Leaderboard
from skillopt_train.providers import (
    MockProvider,
    ScriptedTurn,
    make_json_response,
)
from skillopt_train.skill import Skill
from skillopt_train.skill_train import (
    SkillDrivenConfig,
    SkillDrivenLoop,
)


HELP_TEXT = """
skillopt_train_e2e

Real end-to-end proof that the skill-driven training loop works against a real
Skill bundle and a real eval script

How to run:
    uv run python scripts/skillopt_train_e2e.py

Expected output:
    e2e: skill=holzman-rust step=1 candidate=step-001 mixed=0.4 ok
    e2e: skill=holzman-rust step=2 candidate=step-002 mixed=0.4 ok
    e2e: completed 2 steps best_mixed=0.4 best_candidate=step-001
    e2e: leaderboard entries=2 budget_steps=2 state_step=2
    e2e: OK

Proves:
    SkillDrivenLoop -> Mutator -> eval_bridge.run_eval -> Leaderboard -> Budget
    all wire together against skills/holzman-rust and the real eval.py
"""


def _print(text: str) -> None:
    print(text)


def _step_ok(step: int, candidate: str, mixed: float) -> None:
    _print(f"e2e: skill=holzman-rust step={step} candidate={candidate} mixed={mixed} ok")


def _run_loop(skill: Skill, data_root: Path) -> tuple[int, float, str, int]:
    config = SkillDrivenConfig.from_skill(skill=skill, data_root=data_root)
    provider = MockProvider()
    provider.script(
        ScriptedTurn(
            match="",
            response=make_json_response(
                {
                    "addendum": "tightened cargo fmt enforcement\n",
                    "reasoning": "added strict format check",
                }
            ),
        )
    )
    provider.script(
        ScriptedTurn(
            match="",
            response=make_json_response(
                {
                    "addendum": "added clippy deny rules\n",
                    "reasoning": "tighter lint gates",
                }
            ),
        )
    )
    loop = SkillDrivenLoop(
        config,
        Budget(BudgetConfig.default()),
        Leaderboard(config.leaderboard_path),
        provider,
    )
    entries = loop.run(max_steps=2)
    loop.save_state()
    loop.budget.save(config.budget_path)
    for entry in entries:
        _step_ok(entry.step, entry.candidate, entry.mixed)
    return (
        loop.state.step,
        loop.state.best_mixed,
        loop.state.best_candidate,
        len(loop.leaderboard.all()),
    )


def _report(
    state_step: int,
    best_mixed: float,
    best_candidate: str,
    leaderboard_count: int,
    budget_steps: int,
) -> str:
    _print(
        f"e2e: completed {state_step} steps best_mixed={best_mixed} "
        f"best_candidate={best_candidate}"
    )
    _print(
        f"e2e: leaderboard entries={leaderboard_count} "
        f"budget_steps={budget_steps} state_step={state_step}"
    )
    if state_step == 2 and leaderboard_count >= 2 and budget_steps == 2:
        return "OK"
    return "FAIL"


def main(argv: tuple[str, ...]) -> int:
    if "--help" in argv or "-h" in argv:
        _print(HELP_TEXT)
        return 0
    skill = Skill.find(Path("skills"), "holzman-rust")
    data_root = Path("data/holzman-rust-e2e")
    if data_root.exists():
        for child in data_root.iterdir():
            if child.is_dir() and not child.is_symlink():
                for sub in child.rglob("*"):
                    if sub.is_file():
                        sub.unlink()
                child.rmdir()
            else:
                child.unlink()
    data_root.mkdir(parents=True, exist_ok=True)
    state_step, best_mixed, best_candidate, leaderboard_count = _run_loop(
        skill, data_root
    )
    budget_path = data_root / "budget.json"
    budget_state = Budget.load(BudgetConfig.default(), budget_path).snapshot()
    result = _report(
        state_step, best_mixed, best_candidate, leaderboard_count, budget_state.steps_completed
    )
    _print(f"e2e: {result}")
    return 0 if result == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main(tuple(sys.argv[1:])))