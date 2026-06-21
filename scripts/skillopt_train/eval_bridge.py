from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from .errors import EvalError

DEFAULT_MIN_TIMEOUT_SECONDS: Final[int] = 60
DEFAULT_OPENCODE_TIMEOUT: Final[int] = 300
DEFAULT_CARGO_TIMEOUT: Final[int] = 120
DEFAULT_EVAL_KIND: Final[str] = "all"
SUMMARY_FILE_NAME: Final[str] = "summary.json"
ADDENDUM_FILE_NAME: Final[str] = "SKILL-addendum.md"


class EvalResultDict(TypedDict):
    run_id: str
    candidate_name: str
    candidate_overlay: str
    run_root: str
    summary_path: str
    returncode: int
    timed_out: bool
    hard: float
    soft: float
    mixed: float
    passed_tasks: int
    failed_tasks: int
    gate_action: str


@dataclass(frozen=True, slots=True)
class EvalResult:
    run_id: str
    candidate_name: str
    candidate_overlay: Path
    run_root: Path
    summary_path: Path
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    hard: float
    soft: float
    mixed: float
    passed_tasks: int
    failed_tasks: int
    gate_action: str

    def to_mapping(self) -> EvalResultDict:
        return {
            "run_id": self.run_id,
            "candidate_name": self.candidate_name,
            "candidate_overlay": str(self.candidate_overlay),
            "run_root": str(self.run_root),
            "summary_path": str(self.summary_path),
            "returncode": self.returncode,
            "timed_out": self.timed_out,
            "hard": self.hard,
            "soft": self.soft,
            "mixed": self.mixed,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "gate_action": self.gate_action,
        }


@dataclass(frozen=True, slots=True)
class _ParsedSummary:
    hard: float
    soft: float
    mixed: float
    passed: int
    task_count: int
    gate_action: str


def run_eval(
    *,
    candidate_name: str,
    candidate_overlay: Path,
    run_id: str,
    eval_script: Path,
    repo_root: Path,
    tasks_path: Path,
    runs_root: Path,
    sandbox_root: Path,
    model: str = "",
    opencode_timeout: int = DEFAULT_OPENCODE_TIMEOUT,
    cargo_timeout: int = DEFAULT_CARGO_TIMEOUT,
    limit: int = 0,
    kind: str = DEFAULT_EVAL_KIND,
    task_ids: tuple[str, ...] | None = None,
    python_bin: str = sys.executable,
) -> EvalResult:
    _validate_inputs(eval_script=eval_script, candidate_overlay=candidate_overlay)
    args = _build_eval_args(
        python_bin=python_bin,
        eval_script=eval_script,
        tasks_path=tasks_path,
        candidate_name=candidate_name,
        candidate_overlay=candidate_overlay,
        run_id=run_id,
        sandbox_root=sandbox_root,
        opencode_timeout=opencode_timeout,
        cargo_timeout=cargo_timeout,
        kind=kind,
        model=model,
        limit=limit,
        task_ids=task_ids,
    )
    proc = subprocess.run(
        args,
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
        timeout=max(DEFAULT_MIN_TIMEOUT_SECONDS, opencode_timeout * 4),
    )
    run_root = runs_root / run_id
    summary_path = run_root / SUMMARY_FILE_NAME
    parsed = _parse_summary(summary_path, candidate_name)
    failed_tasks = max(0, parsed.task_count - parsed.passed)
    return EvalResult(
        run_id=run_id,
        candidate_name=candidate_name,
        candidate_overlay=candidate_overlay,
        run_root=run_root,
        summary_path=summary_path,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        timed_out=False,
        hard=parsed.hard,
        soft=parsed.soft,
        mixed=parsed.mixed,
        passed_tasks=parsed.passed,
        failed_tasks=failed_tasks,
        gate_action=parsed.gate_action,
    )


def _validate_inputs(*, eval_script: Path, candidate_overlay: Path) -> None:
    if not eval_script.is_file():
        raise EvalError(
            f"eval script not found: {eval_script}",
            code="script_missing",
            context={"path": str(eval_script)},
        )
    if not candidate_overlay.is_dir():
        raise EvalError(
            f"candidate overlay missing: {candidate_overlay}",
            code="overlay_missing",
            context={"path": str(candidate_overlay)},
        )
    addendum = candidate_overlay / ADDENDUM_FILE_NAME
    if not addendum.is_file():
        raise EvalError(
            f"candidate overlay missing SKILL-addendum.md: {addendum}",
            code="addendum_missing",
            context={"path": str(addendum)},
        )


def _build_eval_args(
    *,
    python_bin: str,
    eval_script: Path,
    tasks_path: Path,
    candidate_name: str,
    candidate_overlay: Path,
    run_id: str,
    sandbox_root: Path,
    opencode_timeout: int,
    cargo_timeout: int,
    kind: str,
    model: str,
    limit: int,
    task_ids: Sequence[str] | None,
) -> list[str]:
    args: list[str] = [
        python_bin,
        str(eval_script),
        "--tasks", str(tasks_path),
        "--candidate-name", candidate_name,
        "--candidate-overlay-dir", str(candidate_overlay),
        "--run-id", run_id,
        "--sandbox-root", str(sandbox_root),
        "--timeout", str(opencode_timeout),
        "--cargo-timeout", str(cargo_timeout),
        "--kind", kind,
    ]
    if model:
        args.extend(["--model", model])
    if limit > 0:
        args.extend(["--limit", str(limit)])
    for task_id in task_ids or ():
        args.extend(["--task-id", task_id])
    return args


def _parse_summary(summary_path: Path, candidate_name: str) -> _ParsedSummary:
    summary = _read_json(summary_path)
    aggregate = _locate_aggregate(summary, candidate_name)
    hard = _as_float(aggregate.get("hard", 0.0), 0.0)
    soft = _as_float(aggregate.get("soft", 0.0), 0.0)
    mixed = _as_float(aggregate.get("mixed", 0.0), 0.0)
    passed = _as_int(aggregate.get("passed_tasks", 0), 0)
    task_count = _as_int(aggregate.get("task_count", 0), 0)
    match summary.get("gate", {}):
        case dict() as gate:
            gate_action = str(gate.get("action", ""))
        case _:
            gate_action = ""
    return _ParsedSummary(
        hard=hard,
        soft=soft,
        mixed=mixed,
        passed=passed,
        task_count=task_count,
        gate_action=gate_action,
    )


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _locate_aggregate(
    summary: Mapping[str, object], candidate_name: str
) -> dict[str, object]:
    aggregates = summary.get("aggregates", [])
    if not isinstance(aggregates, list):
        return {}
    for entry in aggregates:
        if isinstance(entry, dict) and entry.get("bundle") == candidate_name:
            return entry
    for entry in aggregates:
        if isinstance(entry, dict):
            return entry
    return {}


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
