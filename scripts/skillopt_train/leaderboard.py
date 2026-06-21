from __future__ import annotations

import contextlib
import fcntl
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, cast

from .errors import LeaderboardError

_LEADERBOARD_PRUNE_DEFAULT: Final[int] = 1024


class LeaderboardExtras(TypedDict, total=False):
    step: int
    model: str
    attempts: list[str]
    skill: str


class LeaderboardEntryDict(TypedDict, total=False):
    run_id: str
    candidate: str
    step: int
    mixed: float
    hard: float
    soft: float
    usd_spent: float
    wall_seconds: float
    gate_action: str
    bundle_sha256: str
    timestamp: float
    extras: LeaderboardExtras


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    run_id: str
    candidate: str
    step: int
    mixed: float
    hard: float
    soft: float
    usd_spent: float
    wall_seconds: float
    gate_action: str
    bundle_sha256: str
    timestamp: float
    extras: LeaderboardExtras

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> LeaderboardEntry:
        extras_raw = data.get("extras", {})
        extras: LeaderboardExtras
        match extras_raw:
            case Mapping() as m:
                extras = cast(
                    LeaderboardExtras, {str(k): v for k, v in m.items()}
                )
            case _:
                extras = cast(LeaderboardExtras, {})
        return LeaderboardEntry(
            run_id=str(data.get("run_id", "")),
            candidate=str(data.get("candidate", "")),
            step=_as_int(data.get("step", 0), 0),
            mixed=_as_float(data.get("mixed", 0.0), 0.0),
            hard=_as_float(data.get("hard", 0.0), 0.0),
            soft=_as_float(data.get("soft", 0.0), 0.0),
            usd_spent=_as_float(data.get("usd_spent", 0.0), 0.0),
            wall_seconds=_as_float(data.get("wall_seconds", 0.0), 0.0),
            gate_action=str(data.get("gate_action", "")),
            bundle_sha256=str(data.get("bundle_sha256", "")),
            timestamp=_as_float(data.get("timestamp", time.time()), time.time()),
            extras=extras,
        )

    def to_mapping(self) -> LeaderboardEntryDict:
        out: LeaderboardEntryDict = {
            "run_id": self.run_id,
            "candidate": self.candidate,
            "step": self.step,
            "mixed": self.mixed,
            "hard": self.hard,
            "soft": self.soft,
            "usd_spent": self.usd_spent,
            "wall_seconds": self.wall_seconds,
            "gate_action": self.gate_action,
            "bundle_sha256": self.bundle_sha256,
            "timestamp": self.timestamp,
        }
        if self.extras:
            out["extras"] = cast(LeaderboardExtras, dict(self.extras))
        return out


def best_entry(entries: tuple[LeaderboardEntry, ...]) -> LeaderboardEntry | None:
    match entries:
        case ():
            return None
        case _:
            return max(entries, key=lambda e: (e.mixed, e.hard, e.timestamp))


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


def _read_jsonl(path: Path) -> tuple[LeaderboardEntry, ...]:
    if not path.exists():
        return ()
    out: list[LeaderboardEntry] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise LeaderboardError(
                    f"leaderboard.jsonl line {line_number} is not valid JSON",
                    code="jsonl_corrupt",
                    context={"line": str(line_number), "error": str(exc)},
                ) from exc
            match payload:
                case Mapping():
                    out.append(LeaderboardEntry.from_mapping(payload))
                case _:
                    pass
    return tuple(out)


def _locked_append(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        with contextlib.suppress(BlockingIOError, InterruptedError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(line)
            handle.write("\n")
        finally:
            with contextlib.suppress(BlockingIOError, InterruptedError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True, slots=True)
class Leaderboard:
    store: Path

    def __post_init__(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: LeaderboardEntry) -> None:
        if not entry.run_id:
            raise LeaderboardError("entry missing run_id", code="missing_run_id")
        _locked_append(self.store, json.dumps(entry.to_mapping(), sort_keys=True))

    def all(self) -> tuple[LeaderboardEntry, ...]:
        return _read_jsonl(self.store)

    def by_candidate(self, candidate: str) -> tuple[LeaderboardEntry, ...]:
        return tuple(entry for entry in self.all() if entry.candidate == candidate)

    def best(self) -> LeaderboardEntry | None:
        return best_entry(self.all())

    def best_for(self, candidate: str) -> LeaderboardEntry | None:
        return best_entry(self.by_candidate(candidate))

    def history(self, candidate: str) -> tuple[LeaderboardEntry, ...]:
        return tuple(sorted(self.by_candidate(candidate), key=lambda e: e.step))

    def prune(self, keep_last: int = _LEADERBOARD_PRUNE_DEFAULT) -> int:
        entries = self.all()
        if len(entries) <= keep_last:
            return 0
        keep = entries[-keep_last:]
        tmp = self.store.with_suffix(self.store.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for entry in keep:
                handle.write(json.dumps(entry.to_mapping(), sort_keys=True))
                handle.write("\n")
        tmp.replace(self.store)
        return len(entries) - len(keep)


def _render_best(target: LeaderboardEntry | None) -> str:
    match target:
        case None:
            return json.dumps({"empty": True})
        case _:
            return json.dumps(target.to_mapping(), indent=2, sort_keys=True)


def main(store: Path, best: bool, limit: int, candidate: str) -> str:
    lb = Leaderboard(store)
    rows: tuple[LeaderboardEntry, ...]
    match (best, candidate):
        case (True, cand) if cand:
            return _render_best(lb.best_for(cand))
        case (True, ""):
            return _render_best(lb.best())
        case (False, cand) if cand:
            rows = lb.history(cand)
        case _:
            rows = tuple(
                sorted(lb.all(), key=lambda e: e.mixed, reverse=True)
            )[:limit]
    return json.dumps([row.to_mapping() for row in rows], indent=2, sort_keys=True)
