from __future__ import annotations

from skillopt_train.diff_report import FailureBucket
from skillopt_train.self_critique import (
    build_critique,
    inject_critique,
    top_failure_modes,
)


def test_top_failure_modes_ranks_regressions_first() -> None:
    diff = FailureDiff_stub(
        regressions=(FailureBucket(name="cargo:fmt", count=3, examples=("t1",)),),
        improvements=(FailureBucket(name="forbidden:unwrap", count=2, examples=("t2",)),),
    )
    top = top_failure_modes(diff)
    assert top[0].name == "cargo:fmt"
    assert top[1].name == "forbidden:unwrap"


def test_build_critique_empty_diff_produces_no_op_block() -> None:
    diff = FailureDiff_stub()
    critique = build_critique(diff)
    assert "no failure modes" in critique.prompt_section or "Self-Critique" in critique.prompt_section


def test_inject_critique_appends_section() -> None:
    prompt = "Original prompt"
    diff = FailureDiff_stub()
    critique = build_critique(diff)
    injected = inject_critique(prompt, critique)
    assert injected.startswith("Original prompt")
    assert "Self-Critique" in injected


def FailureDiff_stub(  # noqa: N802
    regressions: tuple[FailureBucket, ...] = (),
    improvements: tuple[FailureBucket, ...] = (),
    introduced: tuple[FailureBucket, ...] = (),
    unchanged: tuple[FailureBucket, ...] = (),
) -> object:
    from skillopt_train.diff_report import FailureDiff

    return FailureDiff(
        before_buckets=(),
        after_buckets=regressions + improvements + introduced + unchanged,
        before_hard=0.0,
        after_hard=0.0,
        before_soft=0.0,
        after_soft=0.0,
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        introduced=introduced,
    )