"""Hypothesis property tests for every public pure function in scripts.eval_core."""

from __future__ import annotations

# pyright: reportPrivateUsage=false, reportUnknownLambdaType=false, reportUnknownArgumentType=false
import hashlib
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

import pytest
from beartype import beartype
from expression import Result
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pyrsistent import pmap

from scripts.dataset_core import (
    CountsDict,
    TaskDict,
)
from scripts.errors import EvalError
from scripts.eval_core import (
    _HARD_PASS_THRESHOLD,
    VALID_SPLITS,
    AdapterProtocol,
    BundleHashesDict,
    DataloaderProtocol,
    SummaryDict,
    _adapter_from_cfg,
    _as_float,
    _as_int,
    _as_str,
    _config_errors,
    _display_path,
    _log_failure_lines,
    _prepare_config,
    _promotion_status,
    _resolve_out_root,
    _row_hard,
    _row_passed_p,
    _row_soft,
    _run_metadata,
    _run_split,
    _split_values_postcondition,
    _validate_candidate,
    _validate_splits,
    _validate_supported_config,
    all_split_items,
    bundle_hashes,
    selected_items,
    sha256_file,
    split_values,
    summarize,
)

# --- Test constants ---

_INT_PATTERN: Final[str] = r"[+-]?\d+"
_FLOAT_PATTERN: Final[str] = r"[+-]?\d+(?:\.\d+)?"
_NAME_PATTERN: Final[str] = r"[A-Za-z_][A-Za-z0-9_]*"
_NON_NUMERIC_ALPHABET: Final[str] = "abcdefgijklm"
_MAX_EXAMPLES: Final[int] = 32
_MAX_SMALL_EXAMPLES: Final[int] = 16
_INT_RANGE: Final[int] = 2**16
_FLOAT_BOUND: Final[float] = 1e4
_SHORT_TEXT: Final[int] = 8
_HEX_DIGEST_LEN: Final[int] = 64


# --- Test doubles and strategies ---


class _FakeDataloader:
    """In-memory dataloader used to satisfy the AdapterProtocol in tests."""

    train_items: Sequence[Mapping[str, object]]
    val_items: Sequence[Mapping[str, object]]
    test_items: Sequence[Mapping[str, object]]

    def __init__(
        self,
        train: Sequence[Mapping[str, object]],
        val: Sequence[Mapping[str, object]],
        test: Sequence[Mapping[str, object]],
    ) -> None:
        """Store the per-split item tuples on plain instance attributes."""
        self.train_items = train
        self.val_items = val
        self.test_items = test


class _FakeAdapter:
    """AdapterProtocol double with a no-op ``setup``/``rollout`` pair."""

    dataloader: DataloaderProtocol

    def __init__(self, dataloader: DataloaderProtocol) -> None:
        """Attach the supplied dataloader to satisfy the protocol contract."""
        self.dataloader = dataloader

    def setup(self, cfg: Mapping[str, object]) -> None:
        """No-op stub mirroring the :class:`AdapterProtocol.setup` signature."""
        del cfg

    def rollout(
        self,
        items: Sequence[Mapping[str, object]],
        skill: str,
        out_dir: str,
    ) -> Sequence[Mapping[str, object]]:
        """Return ``items`` unchanged (no-op stub)."""
        del skill, out_dir
        return items


@st.composite
def _dataloader_items(draw: st.DrawFn) -> tuple[Mapping[str, object], ...]:
    """Strategy that builds a tuple of mappings for the fake dataloader."""
    size: int = draw(st.integers(min_value=0, max_value=4))
    return tuple(
        pmap(
            {
                "id": f"task_{index}",
                "kind": draw(st.sampled_from(["review", "repair"])),
                "task_type": draw(st.sampled_from(["review", "repair"])),
                "hard": draw(
                    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
                ),
                "soft": draw(
                    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
                ),
                "fail_reason": draw(st.text(max_size=_SHORT_TEXT)),
                "model": draw(st.text(max_size=_SHORT_TEXT)),
            }
        )
        for index in range(size)
    )


@st.composite
def _adapters(draw: st.DrawFn) -> _FakeAdapter:
    """Strategy that builds a :class:`AdapterProtocol` double for property tests."""
    train: tuple[Mapping[str, object], ...] = draw(_dataloader_items())
    val: tuple[Mapping[str, object], ...] = draw(_dataloader_items())
    test: tuple[Mapping[str, object], ...] = draw(_dataloader_items())
    dataloader: DataloaderProtocol = cast(DataloaderProtocol, _FakeDataloader(train, val, test))
    return _FakeAdapter(dataloader)


# --- _as_int ---


@pytest.mark.property
@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.from_regex(_INT_PATTERN, fullmatch=True),
        st.text(alphabet=_NON_NUMERIC_ALPHABET, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_as_int_coerces(value: object) -> None:
    """Property: ``_as_int`` coerces bool/int/float/regex-matched str to int."""
    result: int = _as_int(value, 0)
    match value:
        case bool() | int():
            if result != int(value):
                pytest.fail(f"expected {int(value)}, got {result}")
        case float():
            if result != int(value):
                pytest.fail(f"expected {int(value)}, got {result}")
        case str() if re.fullmatch(_INT_PATTERN, value):
            if result != int(value):
                pytest.fail(f"expected {int(value)}, got {result}")
        case _:
            if result != 0:
                pytest.fail(f"expected 0, got {result}")


# --- _as_float ---


@pytest.mark.property
@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.from_regex(_FLOAT_PATTERN, fullmatch=True),
        st.text(alphabet=_NON_NUMERIC_ALPHABET, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_as_float_coerces(value: object) -> None:
    """Property: ``_as_float`` coerces bool/int/float/regex-matched str to float."""
    result: float = _as_float(value, 0.0)
    match value:
        case bool():
            if result != float(int(value)):
                pytest.fail(f"expected {float(int(value))}, got {result}")
        case int() | float():
            if result != float(value):
                pytest.fail(f"expected {float(value)}, got {result}")
        case str() if re.fullmatch(_FLOAT_PATTERN, value):
            if result != float(value):
                pytest.fail(f"expected {float(value)}, got {result}")
        case _:
            if result != 0.0:
                pytest.fail(f"expected 0.0, got {result}")


# --- _as_str ---


@pytest.mark.property
@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.text(min_size=1, max_size=_SHORT_TEXT),
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_as_str_coerces(value: object) -> None:
    """Property: ``_as_str`` returns ``str(value)`` for primitives and the default for None."""
    result: str = _as_str(value, "fallback")
    match value:
        case str():
            if result != value:
                pytest.fail(f"expected {value!r}, got {result!r}")
        case bool() | int() | float():
            if result != str(value):
                pytest.fail(f"expected {str(value)!r}, got {result!r}")
        case _:
            if result != "fallback":
                pytest.fail(f"expected 'fallback', got {result!r}")


# --- sha256_file ---


@pytest.mark.property
@given(payload=st.binary(min_size=0, max_size=64))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_sha256_file_hex_property(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    """Property: ``sha256_file`` returns the lowercase 64-char hex SHA-256 digest."""
    monkeypatch.setattr(Path, "read_bytes", lambda _: payload)
    target: Path = tmp_path / "blob.bin"
    digest: str = sha256_file(target)
    expected: str = hashlib.sha256(payload).hexdigest()
    if digest != expected:
        pytest.fail(f"expected {expected}, got {digest}")
    if len(digest) != _HEX_DIGEST_LEN:
        pytest.fail(f"expected 64 hex chars, got {len(digest)}")
    if not all(char in "0123456789abcdef" for char in digest):
        pytest.fail(f"digest contains non-hex chars: {digest!r}")


# --- split_values ---


@pytest.mark.property
@given(value=st.text(max_size=32))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_split_values_returns_clean_parts(tmp_path: Path, value: str) -> None:
    """Property: every emitted part is non-empty and already stripped."""
    del tmp_path
    parts: Sequence[str] = split_values(value)
    for part in parts:
        if part != part.strip():
            pytest.fail(f"part not stripped: {part!r}")
        if not part:
            pytest.fail(f"expected non-empty part in {parts!r}")
        if "," in part:
            pytest.fail(f"part contains comma: {part!r}")


@pytest.mark.property
@given(parts=st.lists(st.sampled_from(["", " ", "\t", "  \t", "\n "]), min_size=1, max_size=4))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_split_values_postcondition_rejects_whitespace_only(
    parts: Sequence[str],
) -> None:
    """Property: the postcondition rejects any empty or whitespace-only part."""
    if _split_values_postcondition(tuple(parts), None):
        pytest.fail(f"expected postcondition to reject whitespace-only parts: {parts!r}")


# --- all_split_items ---


@pytest.mark.property
@given(adapter=_adapters(), split=st.sampled_from(VALID_SPLITS))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_all_split_items_returns_ok_for_known_splits(adapter: _FakeAdapter, split: str) -> None:
    """Property: ``all_split_items`` always returns ``Ok(...)`` for the known splits."""
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    result: Result[Sequence[Mapping[str, object]], EvalError] = all_split_items(
        adapter_typed, split
    )
    if not result.is_ok():
        pytest.fail(f"expected Ok for known split {split!r}, got Error {result.error!r}")
    expected: Sequence[Mapping[str, object]] = getattr(adapter.dataloader, f"{split}_items")
    if result.ok != expected:
        pytest.fail(f"{split} items mismatch")


@pytest.mark.property
@given(
    adapter=_adapters(),
    split=st.text(min_size=1, max_size=8).filter(lambda s: s not in VALID_SPLITS),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_all_split_items_returns_error_for_unknown_split(adapter: _FakeAdapter, split: str) -> None:
    """Property: ``all_split_items`` returns ``Error`` for any split outside the known set."""
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    result: Result[Sequence[Mapping[str, object]], EvalError] = all_split_items(
        adapter_typed, split
    )
    if result.is_ok():
        pytest.fail(f"expected Error for split {split!r}")


# --- selected_items ---


@pytest.mark.property
@given(adapter=_adapters())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_selected_items_kind_all_no_ids(adapter: _FakeAdapter) -> None:
    """Property: kind='all' with empty ids returns the split tuple unchanged."""
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    items: Sequence[Mapping[str, object]] = selected_items(adapter_typed, "val", frozenset(), "all")
    if items != adapter.dataloader.val_items:
        pytest.fail("expected val_items for kind=all with empty ids")


@pytest.mark.property
@given(adapter=_adapters())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_selected_items_filters_by_kind_review(adapter: _FakeAdapter) -> None:
    """Property: kind='review' filters out repair-kind items."""
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    items: Sequence[Mapping[str, object]] = selected_items(
        adapter_typed, "val", frozenset(), "review"
    )
    for item in items:
        item_kind: str = _as_str(item.get("kind") or item.get("task_type") or "review", "")
        if item_kind != "review":
            pytest.fail(f"expected review kind, got {item_kind!r}")


# --- bundle_hashes ---


@pytest.mark.property
@given(skill_text=st.text(min_size=1, max_size=32))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_bundle_hashes_contains_skill_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    skill_text: str,
) -> None:
    """Property: ``bundle_hashes`` always includes a 64-char skill digest."""
    monkeypatch.setattr(Path, "read_bytes", lambda _: skill_text.encode())
    hashes: BundleHashesDict = bundle_hashes(tmp_path)
    skill_digest: str = hashes["skill"]
    if len(skill_digest) != _HEX_DIGEST_LEN:
        pytest.fail(f"expected 64-char hex digest, got {skill_digest!r}")
    if hashes["references"] != {}:
        pytest.fail("expected empty references without a references directory")


# --- _row_hard / _row_soft / _row_passed_p ---


@pytest.mark.property
@given(value=st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_row_hard_default_property(value: float) -> None:
    """Property: ``_row_hard`` returns the row's hard score, defaulting to 0.0."""
    result: float = _row_hard(pmap({"hard": value}))
    if result != value:
        pytest.fail(f"expected {value}, got {result}")
    result_missing: float = _row_hard(pmap())
    if result_missing != 0.0:
        pytest.fail(f"expected 0.0, got {result_missing}")


@pytest.mark.property
@given(value=st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_row_soft_default_property(value: float) -> None:
    """Property: ``_row_soft`` returns the row's soft score, defaulting to 0.0."""
    result: float = _row_soft(pmap({"soft": value}))
    if result != value:
        pytest.fail(f"expected {value}, got {result}")
    result_missing: float = _row_soft(pmap())
    if result_missing != 0.0:
        pytest.fail(f"expected 0.0, got {result_missing}")


@pytest.mark.property
@given(value=st.floats(min_value=-1.0, max_value=2.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_row_passed_p_property(value: float) -> None:
    """Property: ``_row_passed_p`` returns True iff hard >= threshold."""
    result: bool = _row_passed_p(value)
    expected: bool = value >= _HARD_PASS_THRESHOLD
    if result != expected:
        pytest.fail(f"expected {expected}, got {result} for value={value}")


# --- summarize ---


@pytest.mark.property
@given(
    rows=st.lists(
        st.fixed_dictionaries(
            {
                "id": st.text(min_size=1, max_size=_SHORT_TEXT),
                "hard": st.floats(
                    min_value=0.0, max_value=1.5, allow_nan=False, allow_infinity=False
                ),
                "soft": st.floats(
                    min_value=0.0, max_value=1.5, allow_nan=False, allow_infinity=False
                ),
                "fail_reason": st.text(max_size=_SHORT_TEXT),
                "model": st.text(max_size=_SHORT_TEXT),
            }
        ),
        max_size=4,
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_summarize_passes_through_counts(
    rows: Sequence[Mapping[str, object]],
) -> None:
    """Property: ``summarize`` reports the same n and passed counts as the input length."""
    summary: SummaryDict = summarize(
        candidate="cand",
        skill_hash="0" * 64,
        split="val",
        results=rows,
        non_promotable=False,
        promotion_reason="full_val_test_all_tasks",
    )
    if summary["n"] != len(rows):
        pytest.fail(f"expected n={len(rows)}, got {summary['n']}")
    if summary["passed"] + len(summary["failed"]) != len(rows):
        pytest.fail("passed + failed must equal n")
    if summary["candidate"] != "cand":
        pytest.fail("candidate not preserved")
    if summary["split"] != "val":
        pytest.fail("split not preserved")
    if summary["non_promotable"] is not False:
        pytest.fail("non_promotable not preserved")
    if summary["promotion_reason"] != "full_val_test_all_tasks":
        pytest.fail("promotion_reason not preserved")


# --- _promotion_status ---


@pytest.mark.property
@given(kind=st.sampled_from(["all", "review", "repair"]))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_promotable_when_val_test_and_all(
    kind: str,
) -> None:
    """Property: val+test splits with empty ids and kind='all' returns promotable=True."""
    eligible: bool
    reason: str
    eligible, reason = _promotion_status(("val", "test"), frozenset(), kind)
    if kind == "all":
        if not eligible:
            pytest.fail(f"expected promotable for kind=all, got reason={reason!r}")
        if reason != "full_val_test_all_tasks":
            pytest.fail(f"expected 'full_val_test_all_tasks', got {reason!r}")
    else:
        if eligible:
            pytest.fail(f"expected non-promotable for kind={kind}")
        if f"kind={kind}" not in reason:
            pytest.fail(f"expected 'kind={kind}' in reason, got {reason!r}")


@pytest.mark.property
@given(
    splits=st.lists(st.sampled_from(VALID_SPLITS), min_size=1, max_size=3, unique=True).filter(
        lambda xs: tuple(xs) != ("val", "test")
    )
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_non_promotable_for_wrong_splits(
    splits: Sequence[str],
) -> None:
    """Property: any splits other than (val, test) yields a non-promotable verdict."""
    eligible, reason = _promotion_status(tuple(splits), frozenset(), "all")
    if eligible:
        pytest.fail(f"expected non-promotable for splits={splits!r}")
    if "splits_must_be_val_test" not in reason:
        pytest.fail(f"missing 'splits_must_be_val_test' in {reason!r}")


@pytest.mark.property
@given(ids=st.frozensets(st.from_regex(r"[a-z_]+", fullmatch=True), min_size=1, max_size=3))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_non_promotable_when_ids_nonempty(
    ids: frozenset[str],
) -> None:
    """Property: a non-empty targeted-ids set disables promotion."""
    eligible, reason = _promotion_status(("val", "test"), ids, "all")
    if eligible:
        pytest.fail(f"expected non-promotable for ids={ids!r}")
    if "targeted_ids_selected" not in reason:
        pytest.fail(f"missing 'targeted_ids_selected' in {reason!r}")


# --- _validate_splits ---


@pytest.mark.property
@given(splits=st.lists(st.sampled_from(VALID_SPLITS), min_size=0, max_size=3, unique=True))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_validate_splits_ok_for_known_splits(splits: Sequence[str]) -> None:
    """Property: any tuple of known splits returns ``Ok(None)``."""
    result: Result[None, EvalError] = _validate_splits(splits)
    if not result.is_ok():
        pytest.fail(f"expected Ok for splits={splits!r}, got Error {result.error!r}")


@pytest.mark.property
@given(bad=st.text(min_size=1, max_size=8).filter(lambda s: s not in VALID_SPLITS))
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_validate_splits_err_for_unknown_splits(bad: str) -> None:
    """Property: an unknown split name returns ``Error`` carrying the name."""
    result: Result[None, EvalError] = _validate_splits((bad,))
    if result.is_ok():
        pytest.fail(f"expected Error for unknown split {bad!r}")
    err: EvalError = result.error
    if bad not in err.message:
        pytest.fail(f"expected message to mention {bad!r}: {err.message!r}")


# --- _validate_candidate ---


@pytest.mark.property
@given(content=st.text(min_size=0, max_size=32))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_validate_candidate_creates_skill(tmp_path: Path, content: str) -> None:
    """Property: ``_validate_candidate`` always returns Ok for any present SKILL.md."""
    skill: Path = tmp_path / "SKILL.md"
    _ = skill.write_text(content)  # nosemgrep: python.no-file-writes
    result: Result[None, EvalError] = _validate_candidate(tmp_path, str)
    if not result.is_ok():
        pytest.fail(f"expected Ok when SKILL.md is present, got Error {result.error!r}")


@pytest.mark.property
@beartype
def test_validate_candidate_missing_skill(tmp_path: Path) -> None:
    """Property: ``_validate_candidate`` returns Error when SKILL.md is absent."""
    result: Result[None, EvalError] = _validate_candidate(tmp_path, str)
    if result.is_ok():
        pytest.fail("expected Error when SKILL.md is missing")
    err: EvalError = result.error
    if "SKILL.md" not in err.message:
        pytest.fail(f"expected message to mention SKILL.md: {err.message!r}")


# --- _config_errors ---


@pytest.mark.property
@given(suffix=st.from_regex(r"[a-z]+", fullmatch=True))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_config_errors_empty_for_supported_split_dir(tmp_path: Path, suffix: str) -> None:
    """Property: a cfg with the supported split_dir/split_mode/manifest yields no errors."""
    supported: Path = tmp_path / f"dir_{suffix}"
    supported.mkdir(exist_ok=True)  # nosemgrep: python.no-file-writes
    _ = (supported / "manifest.json").write_text("{}")  # nosemgrep: python.no-file-writes
    cfg: Mapping[str, object] = pmap({"split_mode": "split_dir", "split_dir": str(supported)})
    errors: Sequence[str] = _config_errors(cfg, supported, "manifest.json", str)
    if errors:
        pytest.fail(f"expected no errors, got {errors!r}")


# --- _validate_supported_config ---


@pytest.mark.property
@given(suffix=st.from_regex(r"[a-z]+", fullmatch=True))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_validate_supported_config_ok_for_supported_dir(tmp_path: Path, suffix: str) -> None:
    """Property: a cfg with the supported split_dir/split_mode/manifest returns Ok."""
    supported: Path = tmp_path / f"dir_{suffix}"
    supported.mkdir(exist_ok=True)  # nosemgrep: python.no-file-writes
    _ = (supported / "manifest.json").write_text("{}")  # nosemgrep: python.no-file-writes
    cfg: Mapping[str, object] = pmap({"split_mode": "split_dir", "split_dir": str(supported)})
    result: Result[None, EvalError] = _validate_supported_config(
        cfg, supported, "manifest.json", str
    )
    if not result.is_ok():
        pytest.fail(f"expected Ok for supported config, got Error {result.error!r}")


# --- _log_failure_lines ---


@pytest.mark.property
@given(
    hard_value=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    fail_reason=st.text(max_size=_SHORT_TEXT),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_log_failure_lines_format(hard_value: float, fail_reason: str) -> None:
    """Property: every emitted failure line is non-empty and starts with 'FAIL'."""
    row: Mapping[str, object] = pmap(
        {
            "id": "row_x",
            "hard": hard_value,
            "fail_reason": fail_reason,
            "model": "m",
        }
    )
    lines: Sequence[str] = _log_failure_lines("val", (row,))
    if hard_value < _HARD_PASS_THRESHOLD:
        if len(lines) != 1:
            pytest.fail(f"expected one FAIL line, got {lines!r}")
        if not lines[0].startswith("FAIL"):
            pytest.fail(f"expected 'FAIL' prefix, got {lines[0]!r}")
        if "row_x" not in lines[0]:
            pytest.fail(f"expected row id in line: {lines[0]!r}")
    elif lines:
        pytest.fail(f"expected no FAIL line for hard={hard_value}, got {lines!r}")


# --- _run_metadata ---


@pytest.mark.property
@given(
    candidate=st.text(min_size=0, max_size=8),
    config_path_display=st.text(min_size=0, max_size=8),
    dataset_split_dir_display=st.text(min_size=0, max_size=8),
    promotion_eligible=st.booleans(),
    promotion_reason=st.text(min_size=0, max_size=8),
)
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_run_metadata_passes_through_scalars(
    candidate: str,
    config_path_display: str,
    dataset_split_dir_display: str,
    promotion_eligible: bool,
    promotion_reason: str,
) -> None:
    """Property: ``_run_metadata`` echoes scalars and coerces ``opencode_show_thinking`` to bool."""
    hashes: BundleHashesDict = BundleHashesDict(skill="abc", references={})
    metadata: Mapping[str, object] = _run_metadata(
        candidate=candidate,
        candidate_dir_display="cand",
        config_path_display=config_path_display,
        cfg=pmap(
            {
                "review_model": "r",
                "repair_model": "p",
                "opencode_variant": "v",
                "opencode_show_thinking": 1,
            }
        ),
        hashes=hashes,
        config_sha256="sha",
        dataset_split_dir_display=dataset_split_dir_display,
        dataset_manifest_sha256="dsha",
        promotion_eligible=promotion_eligible,
        promotion_reason=promotion_reason,
    )
    if metadata["candidate"] != candidate:
        pytest.fail("candidate not echoed")
    if metadata["config_path"] != config_path_display:
        pytest.fail("config_path not echoed")
    if metadata["dataset_split_dir"] != dataset_split_dir_display:
        pytest.fail("dataset_split_dir not echoed")
    if metadata["promotion_eligible"] != promotion_eligible:
        pytest.fail("promotion_eligible not echoed")
    if metadata["promotion_reason"] != promotion_reason:
        pytest.fail("promotion_reason not echoed")
    if metadata["opencode_show_thinking"] is not True:
        pytest.fail("opencode_show_thinking must coerce to True for truthy input")


# --- _display_path ---


@pytest.mark.property
@given(
    suffix=st.from_regex(r"[a-z]+", fullmatch=True),
    name=st.from_regex(r"[a-z]+\.md", fullmatch=True),
)
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_display_path_in_repo_root(tmp_path: Path, suffix: str, name: str) -> None:
    """Property: paths inside the repo root render as a relative posix string."""
    repo: Path = tmp_path / f"repo_{suffix}"
    nested: Path = repo / "src" / name
    rendered: str = _display_path(nested, repo, tmp_path)
    if "/" not in rendered and rendered != nested.name:
        pytest.fail(f"expected relative posix, got {rendered!r}")


# --- _resolve_out_root ---


@pytest.mark.property
@given(
    leaf=st.from_regex(r"[a-z_]+", fullmatch=True),
)
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_resolve_out_root_relative(tmp_path: Path, leaf: str) -> None:
    """Property: a relative ``args_out`` is resolved under the default report root."""
    out: Path = _resolve_out_root(leaf, tmp_path)
    expected: Path = (tmp_path / leaf).resolve()
    if out != expected:
        pytest.fail(f"expected {expected}, got {out}")


@pytest.mark.property
@given(
    leaf=st.from_regex(r"[a-z_]+", fullmatch=True),
)
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_resolve_out_root_absolute(tmp_path: Path, leaf: str) -> None:
    """Property: an absolute ``args_out`` is returned unchanged."""
    absolute: Path = (tmp_path / leaf).resolve()
    out: Path = _resolve_out_root(str(absolute), tmp_path)
    if out != absolute:
        pytest.fail(f"expected {absolute}, got {out}")


# --- _adapter_from_cfg ---


@pytest.mark.property
@given(adapter=_adapters())
@settings(max_examples=_MAX_EXAMPLES, deadline=None)
@beartype
def test_adapter_from_cfg_returns_caller_adapter(adapter: _FakeAdapter) -> None:
    """Property: ``_adapter_from_cfg`` returns exactly the adapter the factory produced."""
    cfg: Mapping[str, object] = pmap()
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    result: AdapterProtocol = _adapter_from_cfg(cfg, lambda _: adapter_typed)
    if result is not adapter_typed:
        pytest.fail("expected the adapter returned by the factory")


# --- _prepare_config ---


@pytest.mark.property
@given(
    refs_dir_name=st.from_regex(r"refs_[a-z]+", fullmatch=True),
    workers=st.integers(min_value=0, max_value=4),
)
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_prepare_config_injects_references_dir(
    tmp_path: Path, refs_dir_name: str, workers: int
) -> None:
    """Property: ``_prepare_config`` always injects ``references_dir`` and ``workers``."""
    refs_dir: Path = tmp_path / refs_dir_name
    config: Path = tmp_path / "config.yaml"
    _ = config.write_text("")  # nosemgrep: python.no-file-writes
    flat: Mapping[str, object] = pmap({"existing": 1})
    result: Mapping[str, object] = _prepare_config(
        config,
        refs_dir,
        workers,
        lambda _: flat,
        lambda _: {},
    )
    if result.get("references_dir") != str(refs_dir):
        pytest.fail("references_dir not injected")
    if workers > 0 and result.get("workers") != workers:
        pytest.fail("workers not injected when positive")
    if result.get("existing") != 1:
        pytest.fail("flattened keys lost")


# --- _run_split ---


@pytest.mark.property
@given(
    id_value=st.from_regex(r"id_[a-z0-9]+", fullmatch=True),
    hard_value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_run_split_full_path_no_ids(tmp_path: Path, id_value: str, hard_value: float) -> None:
    """Property: ``_run_split`` returns Ok with a ``full_<split>`` path when ids are empty."""
    items: Sequence[Mapping[str, object]] = (pmap({"id": id_value, "hard": hard_value}),)
    dataloader: DataloaderProtocol = cast(DataloaderProtocol, _FakeDataloader((), (), ()))
    adapter: _FakeAdapter = _FakeAdapter(dataloader)
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    result: Result[tuple[Path, Sequence[Mapping[str, object]]], EvalError] = _run_split(
        adapter_typed, "skill", "val", items, frozenset(), tmp_path
    )
    if not result.is_ok():
        pytest.fail(f"expected Ok for non-empty items, got Error {result.error!r}")
    path: Path = result.ok[0]
    rows: Sequence[Mapping[str, object]] = result.ok[1]
    if not path.name.startswith("full_"):
        pytest.fail(f"expected full_ prefix, got {path!r}")
    if len(rows) != len(items):
        pytest.fail("rows length must match items")


@pytest.mark.property
@given(split=st.sampled_from(VALID_SPLITS))
@settings(
    max_examples=_MAX_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_run_split_returns_error_for_empty_items(tmp_path: Path, split: str) -> None:
    """Property: ``_run_split`` returns ``Error`` when items is empty."""
    dataloader: DataloaderProtocol = cast(DataloaderProtocol, _FakeDataloader((), (), ()))
    adapter: _FakeAdapter = _FakeAdapter(dataloader)
    adapter_typed: AdapterProtocol = cast(AdapterProtocol, adapter)
    result: Result[tuple[Path, Sequence[Mapping[str, object]]], EvalError] = _run_split(
        adapter_typed, "skill", split, (), frozenset(), tmp_path
    )
    if result.is_ok():
        pytest.fail("expected Error for empty items")
    err: EvalError = result.error
    if err.code != "empty_selection":
        pytest.fail(f"expected code 'empty_selection', got {err.code!r}")


# Suppress unused-name lint for type aliases that pyright may flag.

_COUNTS_TYPE: type[CountsDict] = CountsDict
_TASK_TYPE: type[TaskDict] = TaskDict
del _COUNTS_TYPE, _TASK_TYPE
