from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypedDict

from .diff_report import FailureBucket, FailureBucketDict, FailureDiff


class CritiqueBlockDict(TypedDict):
    top_failures: list[FailureBucketDict]
    hard_delta: float
    soft_delta: float
    summary: str
    prompt_section: str


_DEFAULT_TOP_K: Final[int] = 3
_MAX_EXAMPLES_IN_LINE: Final[int] = 3
_NO_FAILURE_MODES_NOTE: Final[str] = (
    "- (no failure modes to address; consider tightening the rubric)"
)


@dataclass(frozen=True, slots=True)
class CritiqueBlock:
    top_failures: tuple[FailureBucket, ...]
    hard_delta: float
    soft_delta: float
    summary: str
    prompt_section: str

    def to_mapping(self) -> CritiqueBlockDict:
        return {
            "top_failures": [b.to_mapping() for b in self.top_failures],
            "hard_delta": self.hard_delta,
            "soft_delta": self.soft_delta,
            "summary": self.summary,
            "prompt_section": self.prompt_section,
        }


def top_failure_modes(
    diff: FailureDiff,
    k: int = _DEFAULT_TOP_K,
) -> tuple[FailureBucket, ...]:
    seen: set[str] = set()
    ranked: list[FailureBucket] = []
    for source in (diff.regressions, diff.introduced, diff.after_buckets):
        for bucket in source:
            if bucket.name in seen:
                continue
            ranked.append(bucket)
            seen.add(bucket.name)
            if len(ranked) >= k:
                return tuple(ranked)
    return tuple(ranked)


def _format_bucket_line(bucket: FailureBucket) -> str:
    examples = (
        ", ".join(bucket.examples[:_MAX_EXAMPLES_IN_LINE])
        if bucket.examples
        else "n/a"
    )
    return f"- {bucket.name} (count={bucket.count}) examples: {examples}"


def _format_header(diff: FailureDiff) -> list[str]:
    return [
        "## Self-Critique Block",
        "",
        f"hard_score: {diff.before_hard:.3f} -> {diff.after_hard:.3f} "
        f"(delta {diff.delta_hard:+.3f})",
        f"soft_score: {diff.before_soft:.3f} -> {diff.after_soft:.3f} "
        f"(delta {diff.delta_soft:+.3f})",
        "",
        "### Top failure modes to address",
    ]


def _format_top_failures(top: tuple[FailureBucket, ...]) -> list[str]:
    match top:
        case ():
            return [_NO_FAILURE_MODES_NOTE]
        case _:
            return [_format_bucket_line(b) for b in top]


def _format_regressions(
    regressions: tuple[FailureBucket, ...],
    k: int,
) -> list[str]:
    match regressions:
        case ():
            return []
        case _:
            lines: list[str] = ["", "### Regressions"]
            lines.extend(_format_bucket_line(b) for b in regressions[:k])
            return lines


def _format_introduced(
    introduced: tuple[FailureBucket, ...],
    k: int,
) -> list[str]:
    match introduced:
        case ():
            return []
        case _:
            lines: list[str] = ["", "### Introduced failures"]
            lines.extend(_format_bucket_line(b) for b in introduced[:k])
            return lines


def _summary_for(top: tuple[FailureBucket, ...]) -> str:
    return "; ".join(f"{b.name}={b.count}" for b in top)


def build_critique(
    diff: FailureDiff,
    k: int = _DEFAULT_TOP_K,
) -> CritiqueBlock:
    top = top_failure_modes(diff, k)
    lines: list[str] = [
        *_format_header(diff),
        *_format_top_failures(top),
        *_format_regressions(diff.regressions, k),
        *_format_introduced(diff.introduced, k),
    ]
    return CritiqueBlock(
        top_failures=top,
        hard_delta=diff.delta_hard,
        soft_delta=diff.delta_soft,
        summary=_summary_for(top),
        prompt_section="\n".join(lines) + "\n",
    )


def inject_critique(prompt: str, critique: CritiqueBlock) -> str:
    return prompt.rstrip() + "\n\n" + critique.prompt_section
