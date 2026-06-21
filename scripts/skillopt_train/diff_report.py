from __future__ import annotations

import json
import sys
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict, cast

from .errors import DiffError
from .rubric import Rubric


class FailureBucketDict(TypedDict):
    name: str
    count: int
    examples: list[str]


class FailureDiffDict(TypedDict):
    before_hard: float
    after_hard: float
    delta_hard: float
    before_soft: float
    after_soft: float
    delta_soft: float
    regressions: list[FailureBucketDict]
    improvements: list[FailureBucketDict]
    unchanged: list[FailureBucketDict]
    introduced: list[FailureBucketDict]


_FORBIDDEN_TOKEN_BUCKETS: Final[Mapping[str, str]] = {
    "unsafe": "forbidden:unsafe",
    "unwrap": "forbidden:unwrap",
    "expect": "forbidden:expect",
    "panic": "forbidden:panic",
    "todo": "forbidden:todo",
    "unimplemented": "forbidden:unimplemented",
    "unreachable": "forbidden:unreachable",
    "assert": "forbidden:assert",
    "as_conversions": "forbidden:as",
    "indexing_slicing": "forbidden:indexing",
    "arithmetic_side_effects": "forbidden:arithmetic",
    "string_slice": "forbidden:string_slice",
    "get_unwrap": "forbidden:get_unwrap",
    "panic_in_result_fn": "forbidden:panic_in_result",
    "let_underscore_must_use": "forbidden:let_underscore",
    "dbg_macro": "forbidden:dbg_macro",
}


_GRADE_ISSUE_BUCKETS: Final[Mapping[str, str]] = {
    "json_errors": "schema:invalid_json",
    "mutation_errors": "mutation:file_changed",
    "protected_changed": "mutation:protected_changed",
    "execution_errors": "execution:opencode_failure",
    "forbidden_matches": "forbidden:still_present",
    "missing_groups": "rubric:missing_groups",
}


_GRADE_RETURNCODE_BUCKETS: Final[Mapping[str, str]] = {
    "cargo_fmt_returncode": "cargo:fmt",
    "cargo_clippy_returncode": "cargo:clippy",
    "cargo_test_returncode": "cargo:test",
}


_DEFAULT_SUCCESS_THRESHOLD_HARD: Final[float] = 1.0
_DEFAULT_MAX_EXAMPLES: Final[int] = 5


@dataclass(frozen=True, slots=True)
class FailureBucket:
    name: str
    count: int
    examples: tuple[str, ...]

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> FailureBucket:
        return FailureBucket(
            name=_as_str(data.get("name"), ""),
            count=_as_int(data.get("count"), 0),
            examples=tuple(_example_list(data.get("examples"))),
        )

    def to_mapping(self) -> FailureBucketDict:
        return {
            "name": self.name,
            "count": self.count,
            "examples": list(self.examples),
        }


@dataclass(frozen=True, slots=True)
class FailureDiff:
    before_buckets: tuple[FailureBucket, ...]
    after_buckets: tuple[FailureBucket, ...]
    before_hard: float
    after_hard: float
    before_soft: float
    after_soft: float
    regressions: tuple[FailureBucket, ...]
    improvements: tuple[FailureBucket, ...]
    unchanged: tuple[FailureBucket, ...]
    introduced: tuple[FailureBucket, ...]

    @property
    def delta_hard(self) -> float:
        return self.after_hard - self.before_hard

    @property
    def delta_soft(self) -> float:
        return self.after_soft - self.before_soft

    def to_mapping(self) -> FailureDiffDict:
        return {
            "before_hard": self.before_hard,
            "after_hard": self.after_hard,
            "delta_hard": self.delta_hard,
            "before_soft": self.before_soft,
            "after_soft": self.after_soft,
            "delta_soft": self.delta_soft,
            "regressions": [b.to_mapping() for b in self.regressions],
            "improvements": [b.to_mapping() for b in self.improvements],
            "unchanged": [b.to_mapping() for b in self.unchanged],
            "introduced": [b.to_mapping() for b in self.introduced],
        }


@dataclass(frozen=True, slots=True)
class _Classified:
    regressions: list[FailureBucket]
    improvements: list[FailureBucket]
    unchanged: list[FailureBucket]
    introduced: list[FailureBucket]


@dataclass(frozen=True, slots=True)
class _BucketSources:
    forbidden: Mapping[str, str]
    issue_keys: tuple[tuple[str, str], ...]
    returncode_keys: tuple[tuple[str, str], ...]
    success_threshold_hard: float
    max_examples: int


def _lookup_or_default(
    key: str,
    bucket_map: Mapping[str, str],
    prefix: str,
) -> tuple[str, str]:
    bucket = bucket_map.get(key)
    if bucket is None:
        bucket = f"{prefix}{key}"
    return (key, bucket)


def _build_issue_pairs(
    keys: Sequence[str],
    bucket_map: Mapping[str, str],
    prefix: str,
) -> tuple[tuple[str, str], ...]:
    return tuple(_lookup_or_default(k, bucket_map, prefix) for k in keys)


def _resolve_sources(rubric: Rubric | None) -> _BucketSources:
    match rubric:
        case Rubric() as r:
            forbidden = r.forbidden_tokens if r.forbidden_tokens else _FORBIDDEN_TOKEN_BUCKETS
            issue_pairs = _build_issue_pairs(
                r.grade_issue_keys,
                _GRADE_ISSUE_BUCKETS,
                "grade_issue:",
            )
            if not issue_pairs:
                issue_pairs = tuple(_GRADE_ISSUE_BUCKETS.items())
            returncode_pairs = _build_issue_pairs(
                r.grade_returncode_keys,
                _GRADE_RETURNCODE_BUCKETS,
                "grade_returncode:",
            )
            if not returncode_pairs:
                returncode_pairs = tuple(_GRADE_RETURNCODE_BUCKETS.items())
            return _BucketSources(
                forbidden=forbidden,
                issue_keys=issue_pairs,
                returncode_keys=returncode_pairs,
                success_threshold_hard=r.success_threshold_hard,
                max_examples=r.max_examples,
            )
        case _:
            return _BucketSources(
                forbidden=_FORBIDDEN_TOKEN_BUCKETS,
                issue_keys=tuple(_GRADE_ISSUE_BUCKETS.items()),
                returncode_keys=tuple(_GRADE_RETURNCODE_BUCKETS.items()),
                success_threshold_hard=_DEFAULT_SUCCESS_THRESHOLD_HARD,
                max_examples=_DEFAULT_MAX_EXAMPLES,
            )


def _example_list(value: object) -> Iterable[str]:
    match value:
        case list() as items:
            return (str(v) for v in items)
        case _:
            return ()


def _read_summary(path: Path) -> Mapping[str, object]:
    if not path.exists():
        raise DiffError(
            f"summary not found: {path}",
            code="missing",
            context={"path": str(path)},
        )
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DiffError(
            f"summary is not valid JSON: {path}",
            code="json_decode",
            context={"path": str(path), "error": str(exc)},
        ) from exc
    match loaded:
        case dict():
            return cast(Mapping[str, object], loaded)
        case _:
            raise DiffError(
                f"summary is not an object: {path}",
                code="bad_shape",
                context={"path": str(path)},
            )


def _rows_from_results(results: list[object]) -> list[Mapping[str, object]]:
    out: list[Mapping[str, object]] = []
    for row in results:
        match row:
            case dict():
                out.append(cast(Mapping[str, object], row))
            case _:
                pass
    return out


def _failed_task_row(task_id: object) -> Mapping[str, object]:
    return cast(
        Mapping[str, object],
        {
            "id": task_id,
            "hard": 0,
            "soft": 0.0,
            "fail_reason": "summary_failed",
        },
    )


def _rows_from_summaries(summaries: list[object]) -> list[Mapping[str, object]]:
    out: list[Mapping[str, object]] = []
    for sub in summaries:
        match sub:
            case dict():
                failed = sub.get("failed", [])
                match failed:
                    case list() as ids:
                        out.extend(_failed_task_row(tid) for tid in ids)
                    case _:
                        pass
            case _:
                pass
    return out


def _result_rows(summary: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    match summary.get("results"):
        case list() as results:
            return tuple(_rows_from_results(results))
        case _:
            pass
    match summary.get("summaries"):
        case list() as summaries:
            return tuple(_rows_from_summaries(summaries))
        case _:
            return ()


def _grade_of(row: Mapping[str, object]) -> Mapping[str, object]:
    raw = row.get("grade", {})
    match raw:
        case Mapping() as m:
            return m
        case _:
            return {}


def _extract_forbidden_token(
    grade: Mapping[str, object],
    reason: str,
    forbidden_tokens: Mapping[str, str],
) -> str | None:
    grade_dump = json.dumps(dict(grade), sort_keys=True)
    for raw, bucket_name in forbidden_tokens.items():
        if raw in reason or raw in grade_dump:
            return bucket_name
    return None


def _extract_grade_issues(
    grade: Mapping[str, object],
    issue_keys: Sequence[tuple[str, str]],
    returncode_keys: Sequence[tuple[str, str]],
) -> list[str]:
    if not grade:
        return []
    issues: list[str] = []
    for key, bucket_name in issue_keys:
        if _nonempty_list(grade.get(key)):
            issues.append(bucket_name)
    for key, bucket_name in returncode_keys:
        if _as_int(grade.get(key), 0) != 0:
            issues.append(bucket_name)
    return issues


def categorize(
    results: Iterable[Mapping[str, object]],
    rubric: Rubric | None = None,
) -> tuple[FailureBucket, ...]:
    sources = _resolve_sources(rubric)
    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for row in results:
        if _as_float(row.get("hard"), 0.0) >= sources.success_threshold_hard:
            continue
        task_id = _as_str(row.get("id"), _as_str(row.get("task_id"), "?"))
        reason = _as_str(row.get("fail_reason"), "")
        grade = _grade_of(row)
        match _extract_forbidden_token(grade, reason, sources.forbidden):
            case str() as bucket:
                counts[bucket] += 1
                examples.setdefault(bucket, []).append(task_id)
            case _:
                pass
        for issue in _extract_grade_issues(
            grade,
            sources.issue_keys,
            sources.returncode_keys,
        ):
            counts[issue] += 1
            examples.setdefault(issue, []).append(task_id)
    return tuple(
        FailureBucket(
            name=name,
            count=count,
            examples=tuple(examples.get(name, [])[: sources.max_examples]),
        )
        for name, count in counts.most_common()
    )


def _avg(values: Iterable[Mapping[str, object]], key: str) -> float:
    rows = list(values)
    if not rows:
        return 0.0
    return sum(_as_float(row.get(key), 0.0) for row in rows) / len(rows)


def _classify_all(
    before_buckets: Sequence[FailureBucket],
    after_buckets: Sequence[FailureBucket],
) -> _Classified:
    before_map = {b.name: b.count for b in before_buckets}
    after_map = {b.name: b.count for b in after_buckets}
    after_by_name = {b.name: b for b in after_buckets}
    before_by_name = {b.name: b for b in before_buckets}
    sink = _Classified(regressions=[], improvements=[], unchanged=[], introduced=[])
    for name in sorted(set(before_map) | set(after_map)):
        before_count = before_map.get(name, 0)
        after_count = after_map.get(name, 0)
        bucket = (
            after_by_name.get(name)
            or before_by_name.get(name)
            or FailureBucket(name=name, count=0, examples=())
        )
        match (before_count, after_count):
            case (0, count) if count > 0:
                sink.introduced.append(bucket)
            case (b, a) if a > b:
                sink.regressions.append(bucket)
            case (b, 0) if b > 0:
                sink.improvements.append(bucket)
            case _:
                sink.unchanged.append(bucket)
    return sink


def _sorted_desc(buckets: Sequence[FailureBucket]) -> tuple[FailureBucket, ...]:
    return tuple(sorted(buckets, key=lambda b: b.count, reverse=True))


def diff_runs(
    before: Path,
    after: Path,
    rubric: Rubric | None = None,
) -> FailureDiff:
    effective_rubric = rubric if rubric is not None else Rubric.default()
    before_summary = _read_summary(before)
    after_summary = _read_summary(after)
    before_rows = _result_rows(before_summary)
    after_rows = _result_rows(after_summary)
    before_buckets = categorize(before_rows, effective_rubric)
    after_buckets = categorize(after_rows, effective_rubric)
    classified = _classify_all(before_buckets, after_buckets)
    return FailureDiff(
        before_buckets=before_buckets,
        after_buckets=after_buckets,
        before_hard=_avg(before_rows, "hard"),
        after_hard=_avg(after_rows, "hard"),
        before_soft=_avg(before_rows, "soft"),
        after_soft=_avg(after_rows, "soft"),
        regressions=_sorted_desc(classified.regressions),
        improvements=_sorted_desc(classified.improvements),
        unchanged=_sorted_desc(classified.unchanged),
        introduced=_sorted_desc(classified.introduced),
    )


def _render_table(diff: FailureDiff) -> str:
    lines: list[str] = [
        "# Holzman Failure Diff",
        "",
        "| Bucket | Before | After | Delta |",
        "|---|---:|---:|---:|",
    ]
    before_rows = {b.name: b for b in diff.before_buckets}
    after_names = {b.name for b in diff.after_buckets}
    for bucket in diff.after_buckets:
        before = before_rows.get(bucket.name)
        before_count = before.count if before else 0
        delta = bucket.count - before_count
        lines.append(
            f"| {bucket.name} | {before_count} | {bucket.count} | {delta:+d} |"
        )
    for bucket in diff.before_buckets:
        if bucket.name in after_names:
            continue
        lines.append(
            f"| {bucket.name} | {bucket.count} | 0 | -{bucket.count} |"
        )
    return "\n".join(lines)


def _render_headline(diff: FailureDiff) -> str:
    counts = (
        f"regressions: {len(diff.regressions)}, "
        f"improvements: {len(diff.improvements)}, "
        f"introduced: {len(diff.introduced)}"
    )
    return "\n".join([
        "## Headline",
        f"- hard: {diff.before_hard:.3f} -> {diff.after_hard:.3f} "
        f"(delta {diff.delta_hard:+.3f})",
        f"- soft: {diff.before_soft:.3f} -> {diff.after_soft:.3f} "
        f"(delta {diff.delta_soft:+.3f})",
        f"- {counts}",
    ])


def _render_regressions(diff: FailureDiff) -> str:
    if not diff.regressions:
        return ""
    lines: list[str] = ["", "## Regressions"]
    for bucket in diff.regressions:
        lines.append(
            f"- {bucket.name} (+{bucket.count}) "
            f"e.g. {', '.join(bucket.examples)}"
        )
    return "\n".join(lines)


def _render_improvements(diff: FailureDiff) -> str:
    if not diff.improvements:
        return ""
    lines: list[str] = ["", "## Improvements"]
    for bucket in diff.improvements:
        lines.append(f"- {bucket.name} (-{bucket.count})")
    return "\n".join(lines)


def _render_introduced(diff: FailureDiff) -> str:
    if not diff.introduced:
        return ""
    lines: list[str] = ["", "## Introduced"]
    for bucket in diff.introduced:
        lines.append(f"- {bucket.name} ({bucket.count})")
    return "\n".join(lines)


def render_markdown(diff: FailureDiff, rubric: Rubric | None = None) -> str:
    threshold = (
        rubric.success_threshold_hard if rubric is not None else 1.0
    )
    parts: list[str] = [
        _render_table(diff),
        _render_headline(diff),
        _render_regressions(diff),
        _render_improvements(diff),
        _render_introduced(diff),
        "",
    ]
    if diff.after_hard < threshold:
        parts.append(
            f"_warning: after_hard={diff.after_hard:.3f} "
            f"below threshold {threshold:.3f}_"
        )
        parts.append("")
    return "\n".join(parts)


def main(
    before: Path,
    after: Path,
    out: Path | None,
    rubric: Rubric | None = None,
) -> int:
    effective_rubric = rubric if rubric is not None else Rubric.default()
    diff = diff_runs(before, after, effective_rubric)
    text = render_markdown(diff, effective_rubric)
    match out:
        case None:
            sys.stdout.write(text)
        case _:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
    return 0


def _nonempty_list(value: object) -> bool:
    match value:
        case list() as lst:
            return len(lst) > 0
        case _:
            return False


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


def _as_str(value: object, default: str) -> str:
    match value:
        case str() as s:
            return s
        case bool() | int() | float():
            return str(value)
        case _:
            return default


if __name__ == "__main__":
    raise SystemExit(
        main(
            Path(sys.argv[1]),
            Path(sys.argv[2]),
            Path(sys.argv[3]) if len(sys.argv) > 3 else None,
        )
    )
