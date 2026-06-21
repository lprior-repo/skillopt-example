from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .budget import Budget, BudgetConfig
from .diff_report import FailureDiff, diff_runs
from .errors import (
    BudgetExceeded,
    ConfigError,
    DiffError,
    EvalError,
    MutatorError,
    PlateauReached,
    ProviderError,
    TrainError,
)
from .eval_bridge import EvalResult, run_eval
from .leaderboard import Leaderboard, LeaderboardEntry
from .mutator import MutatorMeta, propose
from .providers import ModelProvider, load_provider
from .self_critique import CritiqueBlock, build_critique


@dataclass(frozen=True, slots=True)
class LoopConfig:
    repo_root: Path
    skill_root: Path
    base_overlay: Path
    candidate_root: Path
    tasks_path: Path
    eval_script: Path
    runs_root: Path
    sandbox_root: Path
    leaderboard_path: Path
    budget_path: Path
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
    def from_mapping(repo_root: Path, data: Mapping[str, object]) -> LoopConfig:
        raw_ids: object = data.get("target_task_ids", [])
        match raw_ids:
            case list() as items:
                target_task_ids: tuple[str, ...] = tuple(
                    str(t) for t in items if isinstance(t, (str, int))
                )
            case _:
                target_task_ids = ()
        return LoopConfig(
            repo_root=repo_root,
            skill_root=repo_root / str(data["skill_root"]),
            base_overlay=repo_root / str(data["base_overlay"]),
            candidate_root=repo_root / str(data["candidate_root"]),
            tasks_path=repo_root / str(data["tasks_path"]),
            eval_script=repo_root / str(data["eval_script"]),
            runs_root=repo_root / str(data["runs_root"]),
            sandbox_root=Path(str(data["sandbox_root"])).expanduser(),
            leaderboard_path=repo_root / str(data["leaderboard_path"]),
            budget_path=repo_root / str(data["budget_path"]),
            provider_spec=str(data.get("provider_spec", "mock:dryrun")),
            eval_model=str(data.get("eval_model", "")),
            opencode_timeout=_as_int(data.get("opencode_timeout"), 300),
            cargo_timeout=_as_int(data.get("cargo_timeout"), 120),
            eval_limit=_as_int(data.get("eval_limit"), 0),
            eval_kind=str(data.get("eval_kind", "all")),
            target_task_ids=target_task_ids,
            max_steps=_as_int(data.get("max_steps"), 4),
            regression_tolerance=_as_float(data.get("regression_tolerance"), 0.01),
        )


@dataclass(frozen=True, slots=True)
class LoopState:
    step: int
    best_mixed: float
    best_candidate: str
    last_candidate: str

    @staticmethod
    def empty() -> LoopState:
        return LoopState(step=0, best_mixed=0.0, best_candidate="", last_candidate="")

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> LoopState:
        return LoopState(
            step=_as_int(data.get("step"), 0),
            best_mixed=_as_float(data.get("best_mixed"), 0.0),
            best_candidate=str(data.get("best_candidate", "")),
            last_candidate=str(data.get("last_candidate", "")),
        )

    def to_mapping(self) -> Mapping[str, int | float | str]:
        return {
            "step": self.step,
            "best_mixed": self.best_mixed,
            "best_candidate": self.best_candidate,
            "last_candidate": self.last_candidate,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.to_mapping(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    @staticmethod
    def load(path: Path) -> LoopState:
        if not path.exists():
            return LoopState.empty()
        data = json.loads(path.read_text(encoding="utf-8"))
        match data:
            case dict() as d:
                return LoopState.from_mapping(d)
            case _:
                return LoopState.empty()


class SkillOptLoop:
    config: LoopConfig
    budget: Budget
    leaderboard: Leaderboard
    provider: ModelProvider
    state: LoopState
    _last_diff: FailureDiff | None

    def __init__(
        self,
        config: LoopConfig,
        budget: Budget,
        leaderboard: Leaderboard,
        provider: ModelProvider,
        state: LoopState | None = None,
    ) -> None:
        self.config = config
        self.budget = budget
        self.leaderboard = leaderboard
        self.provider = provider
        self.state = state if state is not None else LoopState.empty()
        self._last_diff = None

    def _diff_for(self, eval_result: EvalResult) -> FailureDiff | None:
        match self._last_baseline_summary_id():
            case str(bid):
                before_path = self.config.runs_root / bid / "summary.json"
                if not before_path.exists():
                    return None
                try:
                    return diff_runs(before_path, eval_result.summary_path)
                except DiffError:
                    return None
            case _:
                return None

    def _last_baseline_summary_id(self) -> str | None:
        baselines = [e for e in self.leaderboard.all() if e.candidate == "baseline"]
        if not baselines:
            return None
        return max(baselines, key=lambda e: e.timestamp).run_id

    def _record(
        self,
        *,
        eval_result: EvalResult,
        meta: MutatorMeta,
        wall: float,
    ) -> LeaderboardEntry:
        entry = LeaderboardEntry(
            run_id=eval_result.run_id,
            candidate=eval_result.candidate_name,
            step=self.state.step,
            mixed=eval_result.mixed,
            hard=eval_result.hard,
            soft=eval_result.soft,
            usd_spent=meta.cost_usd,
            wall_seconds=wall,
            gate_action=eval_result.gate_action,
            bundle_sha256=meta.bundle_sha256,
            timestamp=time.time(),
            extras={
                "step": self.state.step,
                "model": meta.model,
                "attempts": list(meta.attempts),
            },
        )
        self.leaderboard.append(entry)
        return entry

    def _mutate(
        self,
        critique: CritiqueBlock | None,
        previous_addendum: str,
    ) -> tuple[Path, MutatorMeta]:
        self.config.candidate_root.mkdir(parents=True, exist_ok=True)
        return propose(
            provider=self.provider,
            skill_root=self.config.skill_root,
            candidate_root=self.config.candidate_root,
            base_overlay=self.config.base_overlay,
            step=self.state.step + 1,
            critique=critique,
            previous_addendum=previous_addendum,
        )

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

    def _compute_critique(self) -> CritiqueBlock | None:
        match self._last_diff:
            case FailureDiff() as last_diff:
                return build_critique(last_diff, k=3)
            case _:
                return None

    def _read_previous_addendum(self) -> str:
        match self.state.last_candidate:
            case str(name) if name:
                prev_addendum_path = (
                    self.config.candidate_root / name / "SKILL-addendum.md"
                )
                if prev_addendum_path.is_file():
                    return prev_addendum_path.read_text(encoding="utf-8")
                return ""
            case _:
                return ""

    def _mutate_and_eval(
        self,
        critique: CritiqueBlock | None,
        previous_addendum: str,
    ) -> tuple[EvalResult, MutatorMeta, float]:
        started = time.time()
        overlay, meta = self._mutate(critique, previous_addendum)
        candidate_name = overlay.name
        eval_result = self._eval(candidate_name, overlay)
        if eval_result.returncode != 0:
            raise EvalError(
                f"eval failed rc={eval_result.returncode} for {candidate_name}",
                context={"stderr": eval_result.stderr[:512]},
            )
        return eval_result, meta, time.time() - started

    def step_once(self) -> LeaderboardEntry:
        self.budget.check()
        critique = self._compute_critique()
        previous_addendum = self._read_previous_addendum()
        eval_result, meta, wall = self._mutate_and_eval(critique, previous_addendum)
        candidate_name = eval_result.candidate_name
        self.state = LoopState(
            step=self.state.step + 1,
            best_mixed=self.state.best_mixed,
            best_candidate=self.state.best_candidate,
            last_candidate=candidate_name,
        )
        self.budget.record_step(mixed=eval_result.mixed, usd=meta.cost_usd)
        self._last_diff = self._diff_for(eval_result)
        entry = self._record(eval_result=eval_result, meta=meta, wall=wall)
        if eval_result.mixed > self.state.best_mixed:
            self.state = LoopState(
                step=self.state.step,
                best_mixed=eval_result.mixed,
                best_candidate=candidate_name,
                last_candidate=self.state.last_candidate,
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


def _resolve_repo_root(config_path: Path) -> Path:
    match config_path.parent.name:
        case "configs":
            repo_root = config_path.resolve().parents[1]
        case _:
            repo_root = config_path.resolve().parent
    if not (repo_root / "scripts").is_dir():
        repo_root = config_path.resolve().parent
    return repo_root


def main(config_path: Path, resume: bool) -> int:
    repo_root = _resolve_repo_root(config_path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    match raw:
        case dict() as data:
            pass
        case _:
            raise ConfigError(f"config root must be a JSON object: {config_path}")
    config = LoopConfig.from_mapping(repo_root, data)
    budget_raw: object = data.get("budget", {})
    budget_mapping: Mapping[str, object]
    match budget_raw:
        case dict() as bm:
            budget_mapping = bm
        case _:
            budget_mapping = {}
    budget = Budget.load(BudgetConfig.from_mapping(budget_mapping), config.budget_path)
    leaderboard = Leaderboard(config.leaderboard_path)
    provider = load_provider(config.provider_spec)
    state_path = config.budget_path.parent / "loop_state.json"
    state = LoopState.load(state_path) if resume else LoopState.empty()
    loop = SkillOptLoop(config, budget, leaderboard, provider, state)
    entries = loop.run(max_steps=config.max_steps)
    loop.state.save(state_path)
    loop.budget.save(config.budget_path)
    print(
        json.dumps(
            {
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


def _as_float(value: object, default: float) -> float:
    match value:
        case bool():
            return float(int(value))
        case int() | float():
            return float(value)
        case str():
            try:
                return float(value)
            except ValueError:
                return default
        case _:
            return default


def _as_int(value: object, default: int) -> int:
    match value:
        case bool():
            return int(value)
        case int():
            return int(value)
        case float():
            return int(value)
        case str():
            try:
                return int(value)
            except ValueError:
                return default
        case _:
            return default


DEFAULT_PROVIDER_SPEC: Final[str] = "mock:dryrun"
DEFAULT_REGRESSION_TOLERANCE: Final[float] = 0.01
