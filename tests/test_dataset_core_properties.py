"""Hypothesis property tests for every public pure function in scripts.dataset_core."""

from __future__ import annotations

# pyright: reportPrivateUsage=false, reportUnknownLambdaType=false, reportUnknownArgumentType=false
from collections.abc import Mapping, Sequence
from typing import Final

import pytest
from beartype import beartype
from hypothesis import given, settings
from hypothesis import strategies as st
from pyrsistent import pmap

from scripts.dataset_core import (
    _DEFAULT_DOCTRINES,
    _INT_BOUND,
    CountsDict,
    ForbiddenPattern,
    ForbiddenSpec,
    ManifestDict,
    TaskDict,
    _a_in_range,
    _add_counts_post,
    _as_float_post,
    _as_float_requires,
    _b_in_range,
    _build_tasks_post,
    _count_items_post,
    _relative_squared_post,
    _repair_task_post,
    _review_task_post,
    _scale_counts_post,
    _task_family_key,
    add_counts,
    add_integers,
    black_hat_contract,
    black_hat_expected,
    black_hat_tests,
    build_tasks,
    cargo_toml,
    count_items,
    csv_expected,
    csv_tests,
    empty_counts,
    frame_expected,
    frame_tests,
    header_expected,
    header_tests,
    projected_assignment_error,
    registration_expected,
    registration_tests,
    relative_squared_error,
    repair_task,
    review_task,
    scale_counts,
    split_by_family,
    split_family_id,
    summary_expected,
    summary_tests,
)

# --- Test constants ---

_NAME_PATTERN: Final[str] = r"[a-z_]+"
_TASK_ID_PATTERN: Final[str] = r"[a-z0-9_]+"
_DOMAIN_PATTERN: Final[str] = r"case[0-9]{2}"
_NON_EMPTY_TEXT: Final[int] = 8
_MAX_EXAMPLES: Final[int] = 32
_MAX_SMALL_EXAMPLES: Final[int] = 16
_INT_RANGE: Final[int] = 2**10
_FLOAT_BOUND: Final[float] = 1e3
_SHORT_TEXT: Final[int] = 8
_CSV_GROUPS: Final[int] = 7
_SUMMARY_GROUPS: Final[int] = 10
_FRAME_GROUPS: Final[int] = 6
_HEADER_GROUPS: Final[int] = 7
_REGISTRATION_GROUPS: Final[int] = 8
_BLACK_HAT_GROUPS: Final[int] = 13
_SPLIT_KEYS: Final[tuple[str, ...]] = ("train", "val", "test")
_TARGET_MIN: Final[float] = 1.0


# --- Strategies ---


@st.composite
def _task_dicts(
    draw: st.DrawFn,
    *,
    kind: str | None = None,
) -> TaskDict:
    """Build a :class:`TaskDict` instance for property tests."""
    actual_kind: str = kind if kind is not None else draw(st.sampled_from(["review", "repair"]))
    task_id: str = draw(st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
    family: str = draw(st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
    return TaskDict(
        id=task_id,
        kind=actual_kind,
        family_id=family,
        domain_family_id=family,
        split_family_id=family,
        task_type=actual_kind,
        description=draw(st.text(max_size=_SHORT_TEXT)),
        files=pmap(
            {
                "Cargo.toml": cargo_toml(task_id),
                "src/lib.rs": draw(st.text(max_size=_SHORT_TEXT)),
            }
        ),
        doctrines=(),
        expected_output_groups=(),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )


@st.composite
def _counts_dicts(
    draw: st.DrawFn,
    *,
    bound: int = 100,
) -> CountsDict:
    """Build a :class:`CountsDict` instance for property tests."""
    total: int = draw(st.integers(min_value=0, max_value=bound))
    review: int = draw(st.integers(min_value=0, max_value=total))
    repair: int = total - review
    return CountsDict(total=total, review=review, repair=repair)


@st.composite
def _target_mapping(draw: st.DrawFn) -> Mapping[str, float]:
    """Build a single ``{total, review, repair}`` target mapping for property tests."""
    bound: float = _FLOAT_BOUND
    return pmap(
        {
            "total": draw(
                st.floats(
                    min_value=_TARGET_MIN,
                    max_value=bound,
                    allow_nan=False,
                    allow_infinity=False,
                )
            ),
            "review": draw(
                st.floats(
                    min_value=_TARGET_MIN,
                    max_value=bound,
                    allow_nan=False,
                    allow_infinity=False,
                )
            ),
            "repair": draw(
                st.floats(
                    min_value=_TARGET_MIN,
                    max_value=bound,
                    allow_nan=False,
                    allow_infinity=False,
                )
            ),
        }
    )


@st.composite
def _split_counts_map(draw: st.DrawFn) -> Mapping[str, CountsDict]:
    """Build a ``train/val/test`` mapping of :class:`CountsDict` values."""
    return pmap({split: draw(_counts_dicts()) for split in _SPLIT_KEYS})


@st.composite
def _split_targets_map(draw: st.DrawFn) -> Mapping[str, Mapping[str, float]]:
    """Build a ``train/val/test`` mapping of target mappings."""
    return pmap({split: draw(_target_mapping()) for split in _SPLIT_KEYS})


# --- add_integers ---


@pytest.mark.property
@given(
    a=st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
    b=st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_add_integers_property(a: int, b: int) -> None:
    """Property: ``add_integers(a, b) == a + b``."""
    result: int = add_integers(a, b)
    if result != a + b:
        pytest.fail(f"expected {a + b}, got {result}")


# --- cargo_toml ---


@pytest.mark.property
@given(
    name=st.from_regex(_NAME_PATTERN, fullmatch=True),
    deps=st.text(max_size=64),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_cargo_toml_property(name: str, deps: str) -> None:
    """Property: ``cargo_toml`` renders the standard header followed by ``deps``."""
    result: str = cargo_toml(name, deps)
    if not result.startswith("[package]"):
        pytest.fail(f"expected package header, got {result!r}")
    if f'name = "{name}"' not in result:
        pytest.fail(f"expected crate name {name!r} in {result!r}")
    if not result.endswith(deps):
        pytest.fail(f"expected trailing deps {deps!r}, got {result!r}")


# --- split_family_id ---


@pytest.mark.property
@given(task_id=st.text(min_size=1, max_size=32))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_returns_string(task_id: str) -> None:
    """Property: ``split_family_id`` always returns a string for non-empty input."""
    result: str = split_family_id(task_id)
    if not result:
        pytest.fail("expected non-empty result")


@pytest.mark.property
@given(task_id=st.text(max_size=32))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_idempotent(task_id: str) -> None:
    """Property: ``split_family_id`` is idempotent."""
    once: str = split_family_id(task_id)
    twice: str = split_family_id(once)
    if once != twice:
        pytest.fail(f"not idempotent: {once!r} vs {twice!r}")


# --- csv_tests / summary_tests / frame_tests / header_tests / registration_tests
# --- / black_hat_tests ---


@pytest.mark.property
@given(
    task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    parse_fn=st.from_regex(r"parse_[a-z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_csv_tests_property(task_id: str, parse_fn: str) -> None:
    """Property: ``csv_tests`` always embeds the supplied ``task_id`` and ``parse_fn``."""
    result: str = csv_tests(task_id, parse_fn)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if parse_fn not in result:
        pytest.fail(f"expected parse_fn {parse_fn!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


@pytest.mark.property
@given(task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_summary_tests_property(task_id: str) -> None:
    """Property: ``summary_tests`` embeds ``task_id`` and at least one ``#[test]``."""
    result: str = summary_tests(task_id)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


@pytest.mark.property
@given(task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_frame_tests_property(task_id: str) -> None:
    """Property: ``frame_tests`` embeds ``task_id`` and at least one ``#[test]``."""
    result: str = frame_tests(task_id)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


@pytest.mark.property
@given(task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_header_tests_property(task_id: str) -> None:
    """Property: ``header_tests`` embeds ``task_id`` and at least one ``#[test]``."""
    result: str = header_tests(task_id)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


@pytest.mark.property
@given(task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_registration_tests_property(task_id: str) -> None:
    """Property: ``registration_tests`` embeds ``task_id`` and at least one ``#[test]``."""
    result: str = registration_tests(task_id)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


@pytest.mark.property
@given(
    task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    domain=st.from_regex(_DOMAIN_PATTERN, fullmatch=True),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_black_hat_tests_property(task_id: str, domain: str) -> None:
    """Property: ``black_hat_tests`` embeds task id, domain, and at least one ``#[test]``."""
    result: str = black_hat_tests(task_id, domain)
    if f"use {task_id}" not in result:
        pytest.fail(f"expected use {task_id!r} in {result!r}")
    if domain not in result:
        pytest.fail(f"expected domain {domain!r} in {result!r}")
    if "#[test]" not in result:
        pytest.fail("expected Rust #[test] attribute in rendered suite")


# --- *expected() / black_hat_expected() ---


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_csv_expected_is_seven_groups(unit: None) -> None:
    """Property: ``csv_expected`` always returns exactly 7 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = csv_expected()
    if len(groups) != _CSV_GROUPS:
        pytest.fail(f"expected 7 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_summary_expected_is_ten_groups(unit: None) -> None:
    """Property: ``summary_expected`` always returns exactly 10 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = summary_expected()
    if len(groups) != _SUMMARY_GROUPS:
        pytest.fail(f"expected 10 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_frame_expected_is_six_groups(unit: None) -> None:
    """Property: ``frame_expected`` always returns exactly 6 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = frame_expected()
    if len(groups) != _FRAME_GROUPS:
        pytest.fail(f"expected 6 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_header_expected_is_seven_groups(unit: None) -> None:
    """Property: ``header_expected`` always returns exactly 7 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = header_expected()
    if len(groups) != _HEADER_GROUPS:
        pytest.fail(f"expected 7 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_registration_expected_is_eight_groups(unit: None) -> None:
    """Property: ``registration_expected`` always returns exactly 8 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = registration_expected()
    if len(groups) != _REGISTRATION_GROUPS:
        pytest.fail(f"expected 8 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_black_hat_expected_is_thirteen_groups(unit: None) -> None:
    """Property: ``black_hat_expected`` always returns exactly 13 token groups."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    groups: Sequence[Sequence[str]] = black_hat_expected()
    if len(groups) != _BLACK_HAT_GROUPS:
        pytest.fail(f"expected 13 groups, got {len(groups)}")
    for group in groups:
        if not group:
            pytest.fail("expected non-empty group")


# --- black_hat_contract ---


@pytest.mark.property
@given(domain=st.from_regex(_DOMAIN_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_black_hat_contract_property(domain: str) -> None:
    """Property: ``black_hat_contract`` mentions the domain and the contract headline."""
    result: str = black_hat_contract(domain)
    if domain.title() not in result:
        pytest.fail(f"expected title-cased domain in {result!r}")
    if "Contract" not in result:
        pytest.fail(f"expected 'Contract' header in {result!r}")
    if f"process_{domain}_contract" not in result:
        pytest.fail(f"expected process_{domain}_contract in {result!r}")


# --- review_task ---


@pytest.mark.property
@given(
    task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    family=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    src=st.text(max_size=_SHORT_TEXT),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_review_task_property(task_id: str, family: str, src: str) -> None:
    """Property: ``review_task`` echoes id, kind=review, and the rendered ``Cargo.toml``."""
    expected: Sequence[Sequence[str]] = (("group",),)
    result: TaskDict = review_task(
        task_id=task_id,
        family=family,
        src=src,
        expected=expected,
    )
    if result.id != task_id:
        pytest.fail("id not echoed")
    if result.kind != "review":
        pytest.fail(f"expected kind=review, got {result.kind!r}")
    if result.family_id != split_family_id(task_id):
        pytest.fail("family_id not derived from split_family_id")
    if result.task_type != "review":
        pytest.fail(f"expected task_type=review, got {result.task_type!r}")
    if result.files.get("Cargo.toml") != cargo_toml(task_id):
        pytest.fail("Cargo.toml not echoed")
    if result.files.get("src/lib.rs") != src:
        pytest.fail("src/lib.rs not echoed")
    if result.expected_output_groups != (("group",),):
        pytest.fail("expected_output_groups not echoed")
    if result.doctrines != _DEFAULT_DOCTRINES:
        pytest.fail(f"expected default doctrines, got {result.doctrines!r}")


# --- repair_task ---


@pytest.mark.property
@given(
    task_id=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    family=st.from_regex(_TASK_ID_PATTERN, fullmatch=True),
    src=st.text(max_size=_SHORT_TEXT),
    tests=st.text(max_size=_SHORT_TEXT),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_repair_task_property(task_id: str, family: str, src: str, tests: str) -> None:
    """Property: ``repair_task`` echoes id, kind=repair, src, and tests in ``files``."""
    expected: Sequence[Sequence[str]] = (("group",),)
    result: TaskDict = repair_task(
        task_id=task_id,
        family=family,
        src=src,
        tests=tests,
        expected=expected,
    )
    if result.id != task_id:
        pytest.fail("id not echoed")
    if result.kind != "repair":
        pytest.fail(f"expected kind=repair, got {result.kind!r}")
    if result.task_type != "repair":
        pytest.fail(f"expected task_type=repair, got {result.task_type!r}")
    if result.files.get("Cargo.toml") != cargo_toml(task_id):
        pytest.fail("Cargo.toml not echoed")
    if result.files.get("src/lib.rs") != src:
        pytest.fail("src/lib.rs not echoed")
    if result.files.get("tests/behavior.rs") != tests:
        pytest.fail("tests/behavior.rs not echoed")
    if result.expected_source_groups != (("group",),):
        pytest.fail("expected_source_groups not echoed")
    if result.doctrines != _DEFAULT_DOCTRINES:
        pytest.fail(f"expected default doctrines, got {result.doctrines!r}")


# --- build_tasks ---


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_build_tasks_property(unit: None) -> None:
    """Property: ``build_tasks`` always returns a non-empty sequence of :class:`TaskDict`."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    tasks: Sequence[TaskDict] = build_tasks()
    if not tasks:
        pytest.fail("expected non-empty task list")


# --- empty_counts ---


@pytest.mark.property
@given(st.none())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_empty_counts_property(unit: None) -> None:
    """Property: ``empty_counts`` always returns a zero-valued :class:`CountsDict`."""
    del unit  # silence ARG001 - hypothesis-injected sentinel
    counts: CountsDict = empty_counts()
    if counts.total != 0:
        pytest.fail(f"expected total=0, got {counts.total}")
    if counts.review != 0:
        pytest.fail(f"expected review=0, got {counts.review}")
    if counts.repair != 0:
        pytest.fail(f"expected repair=0, got {counts.repair}")


# --- count_items ---


@pytest.mark.property
@given(
    tasks=st.lists(
        _task_dicts(),
        min_size=0,
        max_size=6,
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_count_items_property(tasks: Sequence[TaskDict]) -> None:
    """Property: ``count_items`` matches the per-kind and total counts of the input."""
    counts: CountsDict = count_items(tasks)
    expected_review: int = sum(1 for task in tasks if task.kind == "review")
    expected_repair: int = sum(1 for task in tasks if task.kind == "repair")
    if counts.total != len(tasks):
        pytest.fail(f"expected total={len(tasks)}, got {counts.total}")
    if counts.review != expected_review:
        pytest.fail(f"expected review={expected_review}, got {counts.review}")
    if counts.repair != expected_repair:
        pytest.fail(f"expected repair={expected_repair}, got {counts.repair}")


# --- scale_counts ---


@pytest.mark.property
@given(
    counts=_counts_dicts(),
    ratio=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_scale_counts_property(counts: CountsDict, ratio: float) -> None:
    """Property: ``scale_counts`` multiplies every field by ``ratio``."""
    scaled: Mapping[str, float] = scale_counts(counts, ratio)
    expected_total: float = float(counts.total) * ratio
    expected_review: float = float(counts.review) * ratio
    expected_repair: float = float(counts.repair) * ratio
    if scaled["total"] != expected_total:
        pytest.fail(f"expected total={expected_total}, got {scaled['total']}")
    if scaled["review"] != expected_review:
        pytest.fail(f"expected review={expected_review}, got {scaled['review']}")
    if scaled["repair"] != expected_repair:
        pytest.fail(f"expected repair={expected_repair}, got {scaled['repair']}")


# --- add_counts ---


@pytest.mark.property
@given(left=_counts_dicts(), right=_counts_dicts())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_add_counts_property(left: CountsDict, right: CountsDict) -> None:
    """Property: ``add_counts`` sums the three fields independently."""
    total: CountsDict = add_counts(left, right)
    if total.total != left.total + right.total:
        pytest.fail("total not summed")
    if total.review != left.review + right.review:
        pytest.fail("review not summed")
    if total.repair != left.repair + right.repair:
        pytest.fail("repair not summed")


# --- relative_squared_error ---


@pytest.mark.property
@given(counts=_counts_dicts(bound=10))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_relative_squared_error_property(counts: CountsDict) -> None:
    """Property: ``relative_squared_error`` sums the three squared relative residuals."""
    target: Mapping[str, float] = pmap(
        {
            "total": 1.0,
            "review": 1.0,
            "repair": 1.0,
        }
    )
    result: float = relative_squared_error(counts, target)
    expected: float = (
        (float(counts.total) - 1.0) ** 2
        + (float(counts.review) - 1.0) ** 2
        + (float(counts.repair) - 1.0) ** 2
    )
    if result != expected:
        pytest.fail(f"expected {expected}, got {result}")


# --- projected_assignment_error ---


@pytest.mark.property
@given(
    target_split=st.sampled_from(_SPLIT_KEYS),
    family_count=_counts_dicts(),
    counts=_split_counts_map(),
    targets=_split_targets_map(),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_projected_assignment_error_property(
    target_split: str,
    family_count: CountsDict,
    counts: Mapping[str, CountsDict],
    targets: Mapping[str, Mapping[str, float]],
) -> None:
    """Property: ``projected_assignment_error`` is non-negative and equals the per-split sum."""
    result: float = projected_assignment_error(
        target_split=target_split,
        family_count=family_count,
        counts=counts,
        targets=targets,
    )
    if result < 0.0:
        pytest.fail(f"expected non-negative, got {result}")
    expected: float = 0.0
    for split in _SPLIT_KEYS:
        observed: CountsDict = (
            add_counts(counts[split], family_count) if split == target_split else counts[split]
        )
        expected += relative_squared_error(observed, targets[split])
    if result != expected:
        pytest.fail(f"expected {expected}, got {result}")


# --- split_by_family ---


@pytest.mark.property
@given(
    tasks=st.lists(
        _task_dicts(),
        min_size=1,
        max_size=6,
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_split_by_family_preserves_total(tasks: Sequence[TaskDict]) -> None:
    """Property: ``split_by_family`` partitions every input task into some split."""
    family_order: Sequence[str] = sorted({task.family_id for task in tasks})
    splits: Mapping[str, Sequence[TaskDict]] = split_by_family(tasks, family_order)
    total_assigned: int = sum(len(items) for items in splits.values())
    if total_assigned != len(tasks):
        pytest.fail(f"expected {len(tasks)} total tasks, got {total_assigned} across splits")


@pytest.mark.property
@given(
    tasks=st.lists(
        _task_dicts(),
        min_size=1,
        max_size=6,
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_split_by_family_keys_match_targets(
    tasks: Sequence[TaskDict],
) -> None:
    """Property: ``split_by_family`` only emits train/val/test split keys."""
    family_order: Sequence[str] = sorted({task.family_id for task in tasks})
    splits: Mapping[str, Sequence[TaskDict]] = split_by_family(tasks, family_order)
    expected_keys: frozenset[str] = frozenset({"train", "val", "test"})
    if frozenset(splits.keys()) != expected_keys:
        pytest.fail(f"expected {expected_keys}, got {set(splits.keys())}")


# --- Postcondition / precondition direct coverage (mutmut survival tests) ---


@beartype
def test_a_in_range_inclusive_bounds() -> None:
    """Property: ``_a_in_range`` accepts both inclusive bounds exactly."""
    if not _a_in_range(_INT_BOUND):
        pytest.fail(f"expected True at upper bound {_INT_BOUND}")
    if not _a_in_range(-_INT_BOUND):
        pytest.fail(f"expected True at lower bound {-_INT_BOUND}")


@beartype
def test_b_in_range_inclusive_bounds() -> None:
    """Property: ``_b_in_range`` accepts both inclusive bounds exactly."""
    if not _b_in_range(_INT_BOUND):
        pytest.fail(f"expected True at upper bound {_INT_BOUND}")
    if not _b_in_range(-_INT_BOUND):
        pytest.fail(f"expected True at lower bound {-_INT_BOUND}")


@beartype
def test_build_tasks_post_empty_is_false() -> None:
    """Property: ``_build_tasks_post`` rejects the empty sequence."""
    if _build_tasks_post(()):
        pytest.fail("expected False for empty sequence")


@pytest.mark.property
@given(tasks=st.lists(_task_dicts(), min_size=1, max_size=1))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_build_tasks_post_single_element_is_true(
    tasks: Sequence[TaskDict],
) -> None:
    """Property: ``_build_tasks_post`` accepts a single-element sequence."""
    if not _build_tasks_post(tuple(tasks)):
        pytest.fail("expected True for single-element sequence")


@beartype
def test_as_float_post_true_arm() -> None:
    """Property: ``_as_float_post`` matches the ``True`` arm with ``result == 1.0``."""
    if not _as_float_post(1.0, True, 99.0):
        pytest.fail("expected True for value=True with result=1.0")


@beartype
def test_as_float_post_false_arm() -> None:
    """Property: ``_as_float_post`` matches the ``False`` arm with ``result == 0.0``."""
    if not _as_float_post(0.0, False, 99.0):
        pytest.fail("expected True for value=False with result=0.0")


@beartype
def test_as_float_post_int_arm() -> None:
    """Property: ``_as_float_post`` matches the int arm by coercing ``value``."""
    if not _as_float_post(2.0, 2, 99.0):
        pytest.fail("expected True for value=2 with result=2.0")


@beartype
def test_as_float_post_str_arm() -> None:
    """Property: ``_as_float_post`` matches the numeric-string arm."""
    if not _as_float_post(1.5, "1.5", 99.0):
        pytest.fail("expected True for value='1.5' with result=1.5")


@beartype
def test_as_float_post_default_arm() -> None:
    """Property: ``_as_float_post`` falls back to ``default`` for unsupported types."""
    if not _as_float_post(0.5, [], 0.5):
        pytest.fail("expected True for unsupported value with result=default")


@beartype
def test_as_float_requires_rejects_unsupported_types() -> None:
    """Property: ``_as_float_requires`` rejects unsupported types like list."""
    if _as_float_requires([]):
        pytest.fail("expected False for value=[]")
    if _as_float_requires(object()):
        pytest.fail("expected False for value=object()")


@beartype
def test_task_family_key_prefers_split_family_id() -> None:
    """Property: ``_task_family_key`` returns ``split_family_id`` when non-empty."""
    task: TaskDict = TaskDict(
        id="a",
        kind="review",
        family_id="fallback",
        domain_family_id="a",
        split_family_id="primary",
        task_type="review",
        description="d",
        files=pmap(),
        doctrines=(),
        expected_output_groups=(),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _task_family_key(task) != "primary":
        pytest.fail("expected split_family_id to win over family_id")


@beartype
def test_task_family_key_falls_back_to_family_id() -> None:
    """Property: ``_task_family_key`` returns ``family_id`` when split_family_id is empty."""
    task: TaskDict = TaskDict(
        id="a",
        kind="review",
        family_id="fallback",
        domain_family_id="a",
        split_family_id="",
        task_type="review",
        description="d",
        files=pmap(),
        doctrines=(),
        expected_output_groups=(),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _task_family_key(task) != "fallback":
        pytest.fail("expected fallback to family_id when split_family_id is empty")


@beartype
def test_count_items_post_rejects_inconsistent_review() -> None:
    """Property: ``_count_items_post`` rejects a ``review`` count that disagrees."""
    items: Sequence[TaskDict] = (
        TaskDict(
            id="a",
            kind="review",
            family_id="a",
            domain_family_id="a",
            split_family_id="a",
            task_type="review",
            description="d",
            files=pmap(),
            doctrines=(),
            expected_output_groups=(),
            expected_source_groups=(),
            forbidden_source_patterns=(),
            forbidden_output_patterns=(),
        ),
    )
    wrong: CountsDict = CountsDict(total=1, review=99, repair=-98)
    if _count_items_post(wrong, items):
        pytest.fail("expected False when review count is wrong")


@beartype
def test_count_items_post_rejects_inconsistent_total() -> None:
    """Property: ``_count_items_post`` rejects a ``total`` count that disagrees."""
    items: Sequence[TaskDict] = (
        TaskDict(
            id="a",
            kind="review",
            family_id="a",
            domain_family_id="a",
            split_family_id="a",
            task_type="review",
            description="d",
            files=pmap(),
            doctrines=(),
            expected_output_groups=(),
            expected_source_groups=(),
            forbidden_source_patterns=(),
            forbidden_output_patterns=(),
        ),
    )
    wrong: CountsDict = CountsDict(total=99, review=1, repair=0)
    if _count_items_post(wrong, items):
        pytest.fail("expected False when total count is wrong")


@beartype
def test_scale_counts_post_rejects_wrong_total() -> None:
    """Property: ``_scale_counts_post`` rejects a wrong ``total`` mapping."""
    counts: CountsDict = CountsDict(total=4, review=2, repair=2)
    if _scale_counts_post({"total": 99.0, "review": 2.0, "repair": 2.0}, counts, 0.5):
        pytest.fail("expected False when total mapping is wrong")


@beartype
def test_scale_counts_post_rejects_wrong_repair() -> None:
    """Property: ``_scale_counts_post`` rejects a wrong ``repair`` mapping."""
    counts: CountsDict = CountsDict(total=4, review=2, repair=2)
    if _scale_counts_post({"total": 2.0, "review": 1.0, "repair": 99.0}, counts, 0.5):
        pytest.fail("expected False when repair mapping is wrong")


@beartype
def test_add_counts_post_rejects_wrong_total() -> None:
    """Property: ``_add_counts_post`` rejects a wrong ``total`` field."""
    left: CountsDict = CountsDict(total=1, review=0, repair=1)
    right: CountsDict = CountsDict(total=1, review=0, repair=1)
    wrong: CountsDict = CountsDict(total=99, review=0, repair=2)
    if _add_counts_post(wrong, left, right):
        pytest.fail("expected False when total field is wrong")


@beartype
def test_add_counts_post_rejects_wrong_repair() -> None:
    """Property: ``_add_counts_post`` rejects a wrong ``repair`` field."""
    left: CountsDict = CountsDict(total=1, review=0, repair=1)
    right: CountsDict = CountsDict(total=1, review=0, repair=1)
    wrong: CountsDict = CountsDict(total=2, review=0, repair=99)
    if _add_counts_post(wrong, left, right):
        pytest.fail("expected False when repair field is wrong")


@beartype
def test_relative_squared_post_uses_per_key_target() -> None:
    """Property: ``_relative_squared_post`` reads each key from the target mapping."""
    observed: CountsDict = CountsDict(total=2, review=1, repair=1)
    target: Mapping[str, float] = pmap({"total": 2.0, "review": 4.0, "repair": 5.0})
    expected: float = (
        (2.0 - 2.0) ** 2 / 2.0**2 + (1.0 - 4.0) ** 2 / 4.0**2 + (1.0 - 5.0) ** 2 / 5.0**2
    )
    if not _relative_squared_post(expected, observed, target):
        pytest.fail("expected True for matching relative squared error")
    if _relative_squared_post(0.0, observed, target):
        pytest.fail("expected False for non-matching relative squared error")


@beartype
def test_review_task_post_rejects_wrong_id() -> None:
    """Property: ``_review_task_post`` rejects a result whose id is wrong."""
    task_id: str = "alpha"
    family: str = "alpha"
    src: str = "src"
    split_key: str = split_family_id(task_id)
    wrong: TaskDict = TaskDict(
        id="other",
        kind="review",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="review",
        description="d",
        files=pmap(
            {
                "Cargo.toml": cargo_toml(task_id),
                "src/lib.rs": src,
            }
        ),
        doctrines=(),
        expected_output_groups=(("g",),),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _review_task_post(wrong, task_id=task_id, family=family, src=src):
        pytest.fail("expected False for wrong id")


@beartype
def test_review_task_post_rejects_wrong_src() -> None:
    """Property: ``_review_task_post`` rejects a result whose src/lib.rs is wrong."""
    task_id: str = "alpha"
    family: str = "alpha"
    src: str = "src"
    split_key: str = split_family_id(task_id)
    wrong: TaskDict = TaskDict(
        id=task_id,
        kind="review",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="review",
        description="d",
        files=pmap(
            {
                "Cargo.toml": cargo_toml(task_id),
                "src/lib.rs": "WRONG_SRC",
            }
        ),
        doctrines=(),
        expected_output_groups=(("g",),),
        expected_source_groups=(),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _review_task_post(wrong, task_id=task_id, family=family, src=src):
        pytest.fail("expected False for wrong src/lib.rs")


@beartype
def test_repair_task_post_rejects_wrong_id() -> None:
    """Property: ``_repair_task_post`` rejects a result whose id is wrong."""
    task_id: str = "alpha"
    family: str = "alpha"
    src: str = "src"
    tests: str = "t"
    split_key: str = split_family_id(task_id)
    wrong: TaskDict = TaskDict(
        id="other",
        kind="repair",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="repair",
        description="d",
        files=pmap(
            {
                "Cargo.toml": cargo_toml(task_id),
                "src/lib.rs": src,
                "tests/behavior.rs": tests,
            }
        ),
        doctrines=(),
        expected_output_groups=(),
        expected_source_groups=(("g",),),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _repair_task_post(wrong, task_id=task_id, family=family, src=src, tests=tests):
        pytest.fail("expected False for wrong id")


@beartype
def test_repair_task_post_rejects_wrong_tests() -> None:
    """Property: ``_repair_task_post`` rejects a result whose tests/behavior.rs is wrong."""
    task_id: str = "alpha"
    family: str = "alpha"
    src: str = "src"
    tests: str = "t"
    split_key: str = split_family_id(task_id)
    wrong: TaskDict = TaskDict(
        id=task_id,
        kind="repair",
        family_id=split_key,
        domain_family_id=family,
        split_family_id=split_key,
        task_type="repair",
        description="d",
        files=pmap(
            {
                "Cargo.toml": cargo_toml(task_id),
                "src/lib.rs": src,
                "tests/behavior.rs": "WRONG_TESTS",
            }
        ),
        doctrines=(),
        expected_output_groups=(),
        expected_source_groups=(("g",),),
        forbidden_source_patterns=(),
        forbidden_output_patterns=(),
    )
    if _repair_task_post(wrong, task_id=task_id, family=family, src=src, tests=tests):
        pytest.fail("expected False for wrong tests/behavior.rs")


# --- ForbiddenSpec.from_dict ---


@pytest.mark.property
@given(
    name=st.text(min_size=1, max_size=16),
    pattern=st.text(min_size=1, max_size=16),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_forbidden_spec_from_dict_property(name: str, pattern: str) -> None:
    """Property: ``ForbiddenSpec.from_dict`` round-trips name/pattern into the dataclass."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name=name, pattern=pattern))
    if spec.name != name:
        pytest.fail(f"expected {name}, got {spec.name}")
    if spec.pattern.pattern != pattern:
        pytest.fail(f"expected {pattern}, got {spec.pattern.pattern}")


# Suppress unused-import lint for type aliases that pyright may flag.

_FORBIDDEN_TYPE: type[ForbiddenPattern] = ForbiddenPattern
_MANIFEST_TYPE: type[ManifestDict] = ManifestDict
del _FORBIDDEN_TYPE, _MANIFEST_TYPE
