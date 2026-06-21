from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from .budget import Budget, BudgetConfig
from .errors import ConfigError, Err, Ok, TrainError
from .leaderboard import Leaderboard, LeaderboardEntry, best_entry
from .providers import load_provider
from .skill import Skill
from .train_loop import (
    DEFAULT_PROVIDER_SPEC,
    DEFAULT_REGRESSION_TOLERANCE,
    LoopConfig,
    LoopState,
    SkillOptLoop,
    _as_float,
    _resolve_repo_root,
)

_CI_USAGE: Final[str] = "usage: python -m skillopt_train.ci_runner CONFIG"


def _load_config(config_path: Path) -> Mapping[str, object]:
    if not config_path.exists():
        raise ConfigError(
            f"config not found: {config_path}",
            context={"path": str(config_path)},
        )
    data = json.loads(config_path.read_text(encoding="utf-8"))
    match data:
        case dict() as d:
            return d
        case _:
            raise ConfigError(
                f"config root must be a JSON object: {config_path}",
                context={"path": str(config_path)},
            )


def _budget_mapping(data: Mapping[str, object]) -> Mapping[str, object]:
    raw: object = data.get("budget", {})
    match raw:
        case dict() as bm:
            return bm
        case _:
            return {}


def _best_mixed(entries: tuple[LeaderboardEntry, ...]) -> float:
    match best_entry(entries):
        case Ok(value=entry):
            return entry.mixed
        case Err():
            return 0.0
        case _:
            return 0.0


def _is_regression(after: float, before: float, tolerance: float) -> bool:
    return after < before - tolerance


def _run_one_step(
    config_path: Path, budget_json: Path | None
) -> Mapping[str, object]:
    data = _load_config(config_path)
    repo_root = _resolve_repo_root(config_path)
    config = LoopConfig.from_mapping(repo_root, data)
    budget_path = budget_json if budget_json is not None else config.budget_path
    leaderboard = Leaderboard(config.leaderboard_path)
    before = _best_mixed(leaderboard.all())
    budget = Budget.load(BudgetConfig.from_mapping(_budget_mapping(data)), budget_path)
    provider = load_provider(str(data.get("provider_spec", DEFAULT_PROVIDER_SPEC)))
    state_path = config.budget_path.parent / "loop_state.json"
    loop = SkillOptLoop(config, budget, leaderboard, provider, LoopState.load(state_path))
    entry = loop.step_once()
    loop.state.save(state_path)
    loop.budget.save(budget_path)
    tolerance: float = _as_float(
        data.get("regression_tolerance"), DEFAULT_REGRESSION_TOLERANCE
    )
    return {
        "step": loop.state.step,
        "entry": entry.to_mapping(),
        "best_before_mixed": before,
        "best_after_mixed": entry.mixed,
        "regression": _is_regression(entry.mixed, before, tolerance),
    }


def main(config_path: Path, budget_json: Path | None) -> int:
    try:
        result = _run_one_step(config_path, budget_json)
    except TrainError as exc:
        print(
            json.dumps(
                {"code": exc.code, "message": str(exc), "context": exc.context},
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if bool(result.get("regression", False)) else 0


def _run_one_step_for_skill(
    skill: Skill,
    data_root: Path,
    provider_spec: str,
) -> Mapping[str, object]:
    from .skill_train import SkillDrivenConfig, SkillDrivenLoop

    config = SkillDrivenConfig.from_skill(
        skill=skill,
        data_root=data_root,
        provider_spec=provider_spec,
    )
    leaderboard = Leaderboard(config.leaderboard_path)
    before = _best_mixed(leaderboard.all())
    budget = Budget.load(BudgetConfig.default(), config.budget_path)
    provider = load_provider(provider_spec)
    loop = SkillDrivenLoop(config, budget, leaderboard, provider, resume=False)
    entry = loop.step_once()
    loop.save_state()
    loop.budget.save(config.budget_path)
    return {
        "skill": skill.name,
        "step": loop.state.step,
        "entry": entry.to_mapping(),
        "best_before_mixed": before,
        "best_after_mixed": entry.mixed,
        "regression": _is_regression(
            entry.mixed, before, DEFAULT_REGRESSION_TOLERANCE
        ),
    }


def main_for_skill(
    skill_name: str,
    skills_root: Path,
    data_root: Path,
    provider_spec: str,
    budget_json: Path | None = None,
) -> int:
    skill = Skill.find(skills_root, skill_name)
    try:
        result = _run_one_step_for_skill(skill, data_root, provider_spec)
    except TrainError as exc:
        print(
            json.dumps(
                {"code": exc.code, "message": str(exc), "context": exc.context},
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if bool(result.get("regression", False)) else 0


if __name__ == "__main__":
    config_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if config_arg is None:
        raise SystemExit(_CI_USAGE)
    raise SystemExit(main(config_arg, None))