from __future__ import annotations

import json
import time
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Final, TypedDict

from .errors import BudgetExceeded, PlateauReached

_HISTORY_LIMIT: Final[int] = 16
_DEFAULT_WALL_CLOCK_SECONDS: Final[float] = 14400.0
_DEFAULT_USD_CAP: Final[float] = 50.0
_DEFAULT_MAX_STEPS: Final[int] = 12
_DEFAULT_PLATEAU_WINDOW: Final[int] = 3
_DEFAULT_PLATEAU_MIN_DELTA: Final[float] = 0.005
_MIN_PLATEAU_WINDOW: Final[int] = 2


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


def _as_float_tuple(value: object) -> tuple[float, ...]:
    match value:
        case list():
            return tuple(_as_float(item, 0.0) for item in value)
        case _:
            return ()


class BudgetStateMapping(TypedDict):
    started_at: float
    elapsed_seconds: float
    usd_spent: float
    steps_completed: int
    best_mixed: float
    best_step: int
    history: list[float]


@dataclass(frozen=True, slots=True)
class BudgetConfig:
    wall_clock_seconds: float
    usd_cap: float
    max_steps: int
    plateau_window: int
    plateau_min_delta: float

    @staticmethod
    def default() -> BudgetConfig:
        return BudgetConfig(
            wall_clock_seconds=_DEFAULT_WALL_CLOCK_SECONDS,
            usd_cap=_DEFAULT_USD_CAP,
            max_steps=_DEFAULT_MAX_STEPS,
            plateau_window=_DEFAULT_PLATEAU_WINDOW,
            plateau_min_delta=_DEFAULT_PLATEAU_MIN_DELTA,
        )

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> BudgetConfig:
        return BudgetConfig(
            wall_clock_seconds=_as_float(
                data.get("wall_clock_seconds"), _DEFAULT_WALL_CLOCK_SECONDS
            ),
            usd_cap=_as_float(data.get("usd_cap"), _DEFAULT_USD_CAP),
            max_steps=_as_int(data.get("max_steps"), _DEFAULT_MAX_STEPS),
            plateau_window=_as_int(data.get("plateau_window"), _DEFAULT_PLATEAU_WINDOW),
            plateau_min_delta=_as_float(
                data.get("plateau_min_delta"), _DEFAULT_PLATEAU_MIN_DELTA
            ),
        )


@dataclass(frozen=True, slots=True)
class BudgetState:
    started_at: float
    elapsed_seconds: float
    usd_spent: float
    steps_completed: int
    best_mixed: float
    best_step: int
    history: tuple[float, ...]

    @staticmethod
    def empty() -> BudgetState:
        return BudgetState(
            started_at=time.time(),
            elapsed_seconds=0.0,
            usd_spent=0.0,
            steps_completed=0,
            best_mixed=0.0,
            best_step=0,
            history=(),
        )

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> BudgetState:
        return BudgetState(
            started_at=_as_float(data.get("started_at"), time.time()),
            elapsed_seconds=_as_float(data.get("elapsed_seconds"), 0.0),
            usd_spent=_as_float(data.get("usd_spent"), 0.0),
            steps_completed=_as_int(data.get("steps_completed"), 0),
            best_mixed=_as_float(data.get("best_mixed"), 0.0),
            best_step=_as_int(data.get("best_step"), 0),
            history=_as_float_tuple(data.get("history"))[-_HISTORY_LIMIT:],
        )

    def to_mapping(self) -> BudgetStateMapping:
        return {
            "started_at": self.started_at,
            "elapsed_seconds": self.elapsed_seconds,
            "usd_spent": self.usd_spent,
            "steps_completed": self.steps_completed,
            "best_mixed": self.best_mixed,
            "best_step": self.best_step,
            "history": list(self.history),
        }

    def with_step(self, *, mixed: float, usd: float, now: float) -> BudgetState:
        new_history: tuple[float, ...] = (*self.history, float(mixed))[-_HISTORY_LIMIT:]
        best_mixed = self.best_mixed
        best_step = self.best_step
        steps_completed = self.steps_completed + 1
        if float(mixed) > best_mixed:
            best_mixed = float(mixed)
            best_step = steps_completed
        return BudgetState(
            started_at=self.started_at,
            elapsed_seconds=max(0.0, now - self.started_at),
            usd_spent=max(0.0, self.usd_spent + max(0.0, float(usd))),
            steps_completed=steps_completed,
            best_mixed=best_mixed,
            best_step=best_step,
            history=new_history,
        )


class Budget:
    config: BudgetConfig
    _state: BudgetState
    _lock: Lock

    def __init__(self, config: BudgetConfig, state: BudgetState | None = None) -> None:
        self.config = config
        self._state = state if state is not None else BudgetState.empty()
        self._lock = Lock()

    def snapshot(self) -> BudgetState:
        with self._lock:
            return self._state

    def time_remaining(self) -> float:
        with self._lock:
            elapsed = time.time() - self._state.started_at
        return max(0.0, self.config.wall_clock_seconds - elapsed)

    def usd_remaining(self) -> float:
        with self._lock:
            return max(0.0, self.config.usd_cap - self._state.usd_spent)

    def steps_remaining(self) -> int:
        with self._lock:
            return max(0, self.config.max_steps - self._state.steps_completed)

    def check(self) -> None:
        with self._lock:
            elapsed = time.time() - self._state.started_at
            wall = elapsed > self.config.wall_clock_seconds
            usd = self._state.usd_spent > self.config.usd_cap
            steps = self._state.steps_completed >= self.config.max_steps
            match (wall, usd, steps):
                case (True, _, _):
                    raise BudgetExceeded(
                        f"wall-clock budget exhausted "
                        f"({elapsed:.0f}s > {self.config.wall_clock_seconds:.0f}s)",
                        context={
                            "elapsed": f"{elapsed:.0f}",
                            "limit": f"{self.config.wall_clock_seconds:.0f}",
                        },
                    )
                case (_, True, _):
                    raise BudgetExceeded(
                        f"USD budget exhausted "
                        f"(${self._state.usd_spent:.2f} > ${self.config.usd_cap:.2f})",
                        context={
                            "spent": f"{self._state.usd_spent:.4f}",
                            "cap": f"{self.config.usd_cap:.4f}",
                        },
                    )
                case (_, _, True):
                    raise BudgetExceeded(
                        f"step budget exhausted "
                        f"({self._state.steps_completed} >= {self.config.max_steps})",
                        context={
                            "steps": str(self._state.steps_completed),
                            "max": str(self.config.max_steps),
                        },
                    )
                case _:
                    return None

    def record_step(self, *, mixed: float, usd: float) -> BudgetState:
        with self._lock:
            updated = self._state.with_step(mixed=mixed, usd=usd, now=time.time())
            self._state = updated
            return updated

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with self._lock:
            payload = self._state.to_mapping()
        tmp.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        tmp.replace(path)

    @staticmethod
    def load(config: BudgetConfig, path: Path) -> Budget:
        if not path.exists():
            return Budget(config)
        data = json.loads(path.read_text(encoding="utf-8"))
        match data:
            case dict() as d:
                return Budget(config, BudgetState.from_mapping(d))
            case _:
                return Budget(config)


class PlateauDetector:
    _window: int
    _min_delta: float
    _buf: deque[float]

    def __init__(self, window: int, min_delta: float) -> None:
        if window < _MIN_PLATEAU_WINDOW:
            raise ValueError(f"plateau_window must be >= {_MIN_PLATEAU_WINDOW}")
        if min_delta < 0.0:
            raise ValueError("plateau_min_delta must be >= 0")
        self._window = window
        self._min_delta = min_delta
        self._buf = deque(maxlen=window)

    def update(self, score: float) -> bool:
        self._buf.append(float(score))
        if len(self._buf) < self._window:
            return False
        deltas: list[float] = [
            abs(self._buf[i] - self._buf[i - 1]) for i in range(1, len(self._buf))
        ]
        max_delta = max(deltas) if deltas else 0.0
        return max_delta < self._min_delta

    def last_window(self) -> tuple[float, ...]:
        return tuple(self._buf)

    def check_stream(self, scores: Iterable[float]) -> None:
        for score in scores:
            if self.update(float(score)):
                raise PlateauReached(
                    f"plateau reached: no improvement > {self._min_delta} "
                    f"in last {self._window} steps",
                    context={
                        "window": str(self._window),
                        "min_delta": f"{self._min_delta}",
                    },
                )
