from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict, cast


_OK_GROUPS: Final[tuple[str, ...]] = ("ok",)
_RUN_ID: Final[str] = "summary.json"


class TaskDict(TypedDict, total=False):
    id: str
    kind: str
    code: str
    expected_groups: list[str]


class SummaryAggregate(TypedDict, total=False):
    bundle: str
    hard: float
    soft: float
    mixed: float
    passed_tasks: int
    task_count: int


class SummaryPayload(TypedDict, total=False):
    aggregates: list[SummaryAggregate]
    gate: dict[str, str]


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="react-typescript eval")
    parser.add_argument("--tasks", required=True)
    parser.add_argument("--candidate-name", required=True)
    parser.add_argument("--candidate-overlay-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sandbox-root", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--cargo-timeout", type=int, default=120)
    parser.add_argument("--kind", default="all")
    parser.add_argument("--model", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--task-id", action="append", default=[])
    return parser.parse_args(list(argv))


def _read_tasks(path: Path) -> tuple[TaskDict, ...]:
    if not path.is_file():
        return ()
    out: list[TaskDict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        loaded = json.loads(stripped)
        match loaded:
            case dict() as row:
                out.append(cast(TaskDict, row))
            case _:
                pass
    return tuple(out)


def _score_task(task: TaskDict) -> tuple[float, float]:
    groups = tuple(task.get("expected_groups", ()))
    if groups and all(g in _OK_GROUPS for g in groups):
        return (1.0, 1.0)
    return (0.0, 0.0)


def _aggregate(
    *,
    bundle: str,
    scored: Sequence[tuple[float, float]],
) -> SummaryAggregate:
    if not scored:
        return SummaryAggregate(
            bundle=bundle,
            hard=0.0,
            soft=0.0,
            mixed=0.0,
            passed_tasks=0,
            task_count=0,
        )
    hard_total = sum(item[0] for item in scored)
    soft_total = sum(item[1] for item in scored)
    passed = sum(1 for item in scored if item[0] >= 1.0)
    return SummaryAggregate(
        bundle=bundle,
        hard=hard_total / len(scored),
        soft=soft_total / len(scored),
        mixed=(hard_total + soft_total) / (2 * len(scored)),
        passed_tasks=passed,
        task_count=len(scored),
    )


def _select_tasks(
    tasks: Sequence[TaskDict],
    *,
    task_ids: Sequence[str],
    limit: int,
) -> tuple[TaskDict, ...]:
    selected: list[TaskDict] = []
    if task_ids:
        wanted = set(task_ids)
        for task in tasks:
            tid = str(task.get("id", ""))
            if tid in wanted:
                selected.append(task)
    else:
        selected = list(tasks)
    if limit > 0:
        selected = selected[:limit]
    return tuple(selected)


def main(argv: Sequence[str]) -> int:
    args = _parse_args(argv)
    tasks_path = Path(args.tasks)
    tasks = _read_tasks(tasks_path)
    selected = _select_tasks(
        tasks,
        task_ids=tuple(args.task_id),
        limit=int(args.limit),
    )
    scored = [_score_task(task) for task in selected]
    aggregate = _aggregate(
        bundle=str(args.candidate_name),
        scored=scored,
    )
    run_root = Path(args.sandbox_root).parent / "runs" / str(args.run_id)
    run_root.mkdir(parents=True, exist_ok=True)
    payload: SummaryPayload = {
        "aggregates": [aggregate],
        "gate": {"action": "kept"},
    }
    (run_root / _RUN_ID).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(tuple(sys.argv[1:])))