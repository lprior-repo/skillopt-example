from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .budget import Budget, BudgetConfig
from .errors import (
    BudgetExceeded,
    ConfigError,
    EvalError,
    MutatorError,
    PlateauReached,
    ProviderError,
    TrainError,
)
from .eval_bridge import EvalResult, run_eval
from .leaderboard import Leaderboard, LeaderboardEntry
from .mutator import Mutator, MutatorMeta
from .providers import ModelProvider, load_provider
from .self_critique import CritiqueBlock, build_critique
from .skill import Skill
from .train_loop import (
    DEFAULT_PROVIDER_SPEC,
    DEFAULT_REGRESSION_TOLERANCE,
)

_DEFAULT_OPENCODE_TIMEOUT: Final[int] = 300
_DEFAULT_CARGO_TIMEOUT: Final[int] = 120
_DEFAULT_MAX_STEPS: Final[int] = 4
_DEFAULT_EVAL_LIMIT: Final[int] = 0
_DEFAULT_EVAL_KIND: Final[str] = "all"
_DEFAULT_WALL_CLOCK_SECONDS: Final[float] = 14400.0
_DEFAULT_USD_CAP: Final[float] = 50.0
_DEFAULT_BUDGET_MAX_STEPS: Final[int] = 12
_DEFAULT_PLATEAU_WINDOW: Final[int] = 3
_DEFAULT_PLATEAU_MIN_DELTA: Final[float] = 0.005


def _as_int(value: object, default: int) -> int:
    match value:
        case bool():
            return int(value)
        case int():
            return int(value)
        case float():
            return int(value)
        case str() as s:
            try:
                return int(s)
            except ValueError:
                return default
        case _:
            return default


def _as_float(value: object, default: float) -> float:
    match value:
        case bool():
            return float(int(value))
        case int() | float():
            return float(value)
        case str() as s:
            try:
                return float(s)
            except ValueError:
                return default
        case _:
            return default


@dataclass(frozen=True, slots=True)
class SkillDrivenConfig:
    skill: Skill
    candidate_root: Path
    base_overlay: Path
    runs_root: Path
    sandbox_root: Path
    leaderboard_path: Path
    budget_path: Path
    state_path: Path
    eval_script: Path
    tasks_path: Path
    repo_root: Path
    provider_spec: str
    eval_model: str
    opencode_timeout: int
    cargo_timeout: int
    eval_limit: int
    eval_kind: str
    target_task_ids: tuple[str, ...]
    max_steps: int
    regression_tolerance: float

    @staticmethod
    def from_skill(
        skill: Skill,
        data_root: Path,
        *,
        max_steps: int = _DEFAULT_MAX_STEPS,
        provider_spec: str = DEFAULT_PROVIDER_SPEC,
        repo_root: Path | None = None,
    ) -> SkillDrivenConfig:
        default_cfg = skill.load_default_config()
        resolved_steps = _as_int(default_cfg.get("max_steps"), max_steps)
        if resolved_steps <= 0:
            resolved_steps = max_steps
        resolved_provider = str(default_cfg.get("provider_spec", provider_spec))
        resolved_eval_model = str(default_cfg.get("eval_model", ""))
        resolved_opencode = _as_int(
            default_cfg.get("opencode_timeout"), _DEFAULT_OPENCODE_TIMEOUT
        )
        resolved_cargo = _as_int(
            default_cfg.get("cargo_timeout"), _DEFAULT_CARGO_TIMEOUT
        )
        resolved_regression = _as_float(
            default_cfg.get("regression_tolerance"), DEFAULT_REGRESSION_TOLERANCE
        )
        candidate_root = data_root / "candidates"
        base_overlay = data_root / "overlay"
        runs_root = data_root / "runs"
        sandbox_root = data_root / "sandbox"
        leaderboard_path = data_root / "leaderboard.jsonl"
        budget_path = data_root / "budget.json"
        state_path = data_root / "loop_state.json"
        eval_script = skill.eval_module if skill.eval_module is not None else skill.eval_script
        if eval_script is None:
            raise ConfigError(
                f"skill {skill.name!r} missing eval.py or eval.sh",
                code="skill_no_eval",
                context={"skill": skill.name},
            )
        resolved_repo = repo_root if repo_root is not None else Path.cwd()
        return SkillDrivenConfig(
            skill=skill,
            candidate_root=candidate_root,
            base_overlay=base_overlay,
            runs_root=runs_root,
            sandbox_root=sandbox_root,
            leaderboard_path=leaderboard_path,
            budget_path=budget_path,
            state_path=state_path,
            eval_script=eval_script,
            tasks_path=skill.tasks_path,
            repo_root=resolved_repo,
            provider_spec=resolved_provider,
            eval_model=resolved_eval_model,
            opencode_timeout=resolved_opencode,
            cargo_timeout=resolved_cargo,
            eval_limit=_DEFAULT_EVAL_LIMIT,
            eval_kind=_DEFAULT_EVAL_KIND,
            target_task_ids=(),
            max_steps=resolved_steps,
            regression_tolerance=resolved_regression,
        )


@dataclass(frozen=True, slots=True)
class SkillDrivenState:
    step: int = 0
    best_mixed: float = 0.0
    best_candidate: str = ""
    last_candidate: str = ""

    def with_step(self, *, candidate: str) -> SkillDrivenState:
        return SkillDrivenState(
            step=self.step + 1,
            best_mixed=self.best_mixed,
            best_candidate=self.best_candidate,
            last_candidate=candidate,
        )

    def with_best(self, *, mixed: float, candidate: str) -> SkillDrivenState:
        return SkillDrivenState(
            step=self.step,
            best_mixed=mixed,
            best_candidate=candidate,
            last_candidate=self.last_candidate,
        )

    def to_mapping(self) -> Mapping[str, int | float | str]:
        return {
            "step": self.step,
            "best_mixed": self.best_mixed,
            "best_candidate": self.best_candidate,
            "last_candidate": self.last_candidate,
        }

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> SkillDrivenState:
        return SkillDrivenState(
            step=_as_int(data.get("step"), 0),
            best_mixed=_as_float(data.get("best_mixed"), 0.0),
            best_candidate=str(data.get("best_candidate", "")),
            last_candidate=str(data.get("last_candidate", "")),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_mapping(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def load(path: Path) -> SkillDrivenState:
        if not path.exists():
            return SkillDrivenState()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return SkillDrivenState()
        match data:
            case Mapping() as m:
                return SkillDrivenState.from_mapping(m)
            case _:
                return SkillDrivenState()


class SkillDrivenLoop:
    config: SkillDrivenConfig
    mutator: Mutator
    state: SkillDrivenState
    _budget: Budget
    _leaderboard: Leaderboard
    _provider: ModelProvider
    _last_critique: CritiqueBlock | None

    def __init__(
        self,
        config: SkillDrivenConfig,
        budget: Budget,
        leaderboard: Leaderboard,
        provider: ModelProvider,
        *,
        resume: bool = False,
    ) -> None:
        self.config = config
        self._budget = budget
        self._leaderboard = leaderboard
        self._provider = provider
        self.mutator = Mutator.from_skill(
            skill=config.skill,
            provider=provider,
            candidate_root=config.candidate_root,
            base_overlay=config.base_overlay,
        )
        if resume and config.state_path.is_file():
            self.state = SkillDrivenState.load(config.state_path)
        else:
            self.state = SkillDrivenState()
        self._last_critique = None

    @property
    def budget(self) -> Budget:
        return self._budget

    @property
    def leaderboard(self) -> Leaderboard:
        return self._leaderboard

    @property
    def provider(self) -> ModelProvider:
        return self._provider

    def _read_previous_addendum(self) -> str:
        match self.state.last_candidate:
            case str(name) if name:
                prev_path = self.config.candidate_root / name / "SKILL-addendum.md"
                if prev_path.is_file():
                    return prev_path.read_text(encoding="utf-8")
                return ""
            case _:
                return ""

    def _eval(self, candidate_name: str, candidate_overlay: Path) -> EvalResult:
        run_id = f"step-{self.state.step + 1:03d}-{int(time.time())}"
        return run_eval(
            candidate_name=candidate_name,
            candidate_overlay=candidate_overlay,
            run_id=run_id,
            eval_script=self.config.eval_script,
            repo_root=self.config.repo_root,
            tasks_path=self.config.tasks_path,
            runs_root=self.config.runs_root,
            sandbox_root=self.config.sandbox_root,
            model=self.config.eval_model,
            opencode_timeout=self.config.opencode_timeout,
            cargo_timeout=self.config.cargo_timeout,
            limit=self.config.eval_limit,
            kind=self.config.eval_kind,
            task_ids=self.config.target_task_ids,
        )

    def _record(
        self,
        eval_result: EvalResult,
        meta: MutatorMeta,
    ) -> LeaderboardEntry:
        entry = LeaderboardEntry(
            run_id=eval_result.run_id,
            candidate=eval_result.candidate_name,
            step=self.state.step,
            mixed=eval_result.mixed,
            hard=eval_result.hard,
            soft=eval_result.soft,
            usd_spent=meta.cost_usd,
            wall_seconds=0.0,
            gate_action=eval_result.gate_action,
            bundle_sha256=meta.bundle_sha256,
            timestamp=time.time(),
            extras={
                "step": self.state.step,
                "model": meta.model,
                "attempts": list(meta.attempts),
                "skill": self.config.skill.name,
            },
        )
        self._leaderboard.append(entry)
        return entry

    def step_once(self) -> LeaderboardEntry:
        overlay, meta = self.mutator.propose(
            step=self.state.step + 1,
            critique=self._last_critique,
            previous_addendum=self._read_previous_addendum(),
        )
        candidate_name = overlay.name
        eval_result = self._eval(candidate_name, overlay)
        if eval_result.returncode != 0:
            raise EvalError(
                f"eval failed rc={eval_result.returncode} for {candidate_name}",
                context={"stderr": eval_result.stderr[:512]},
            )
        self.state = self.state.with_step(candidate=candidate_name)
        self._budget.record_step(mixed=eval_result.mixed, usd=meta.cost_usd)
        self._last_critique = self._build_critique(eval_result)
        entry = self._record(eval_result, meta)
        if eval_result.mixed > self.state.best_mixed:
            self.state = self.state.with_best(
                mixed=eval_result.mixed, candidate=candidate_name
            )
        return entry

    def run(self, max_steps: int = 1) -> tuple[LeaderboardEntry, ...]:
        out: list[LeaderboardEntry] = []
        try:
            for _ in range(max(0, max_steps)):
                self.budget.check()
                out.append(self.step_once())
        except (BudgetExceeded, PlateauReached, TrainError, MutatorError, EvalError, ProviderError):
            pass
        return tuple(out)

    def save_state(self) -> None:
        self.state.save(self.config.state_path)

    def _build_critique(self, eval_result: EvalResult) -> CritiqueBlock | None:
        summary_path = eval_result.summary_path
        if not summary_path.is_file():
            return None
        baseline_id = self._baseline_run_id()
        if baseline_id is None:
            return None
        baseline_path = self.config.runs_root / baseline_id / "summary.json"
        if not baseline_path.is_file():
            return None
        try:
            from .diff_report import diff_runs

            diff = diff_runs(baseline_path, summary_path, self.config.skill.rubric)
            return build_critique(diff, k=3)
        except Exception:
            return None

    def _baseline_run_id(self) -> str | None:
        baselines = [e for e in self._leaderboard.all() if e.candidate == "baseline"]
        if not baselines:
            return None
        return max(baselines, key=lambda e: e.timestamp).run_id


def _default_budget_mapping() -> Mapping[str, object]:
    return {
        "wall_clock_seconds": _DEFAULT_WALL_CLOCK_SECONDS,
        "usd_cap": _DEFAULT_USD_CAP,
        "max_steps": _DEFAULT_BUDGET_MAX_STEPS,
        "plateau_window": _DEFAULT_PLATEAU_WINDOW,
        "plateau_min_delta": _DEFAULT_PLATEAU_MIN_DELTA,
    }


def main(
    *,
    skill: Skill,
    data_root: Path,
    provider_spec: str = DEFAULT_PROVIDER_SPEC,
    max_steps: int = _DEFAULT_MAX_STEPS,
    resume: bool = False,
    repo_root: Path | None = None,
) -> int:
    config = SkillDrivenConfig.from_skill(
        skill,
        data_root,
        max_steps=max_steps,
        provider_spec=provider_spec,
        repo_root=repo_root,
    )
    budget = Budget.load(
        BudgetConfig.from_mapping(_default_budget_mapping()),
        config.budget_path,
    )
    leaderboard = Leaderboard(config.leaderboard_path)
    provider = load_provider(config.provider_spec)
    loop = SkillDrivenLoop(
        config, budget, leaderboard, provider, resume=resume
    )
    entries = loop.run(max_steps=config.max_steps)
    loop.save_state()
    loop.budget.save(config.budget_path)
    print(
        json.dumps(
            {
                "skill": skill.name,
                "step": loop.state.step,
                "best_mixed": loop.state.best_mixed,
                "best_candidate": loop.state.best_candidate,
                "last_candidate": loop.state.last_candidate,
                "entries": [e.to_mapping() for e in entries],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def list_skills(skills_root: Path) -> int:
    skills = Skill.discover(skills_root)
    payload: list[dict[str, object]] = []
    for skill in skills:
        payload.append(
            {
                "name": skill.name,
                "path": str(skill.path),
                "rubric": skill.rubric.name,
                "has_eval_py": skill.eval_module is not None,
                "has_eval_sh": skill.eval_script is not None,
                "config": dict(skill.load_default_config()),
            }
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
