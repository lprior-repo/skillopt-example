"""Hypothesis property tests and example regression pins for the rubric and eval core."""

from __future__ import annotations

# pyright: reportPrivateUsage=false, reportUnknownLambdaType=false, reportUnknownArgumentType=false
import dataclasses
import hashlib
import re
from pathlib import Path
from typing import Final

import pytest
from beartype import beartype
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from scripts.generate_holzman_rust_dataset import (
    ForbiddenPattern,
    ForbiddenSpec,
    split_family_id,
)
from scripts.run_holzman_candidate_eval import (
    _HARD_PASS_THRESHOLD,
    _VALID_SPLITS,
    BundleHashesDict,
    CandidatePaths,
    RunError,
    _as_float,
    _as_int,
    _as_str,
    _promotion_status,
    bundle_hashes,
    sha256_file,
    split_values,
)

_EXPECTED_HARD_THRESHOLD: Final[float] = 1.0
_EXPECTED_VALID_SPLITS: Final[tuple[str, ...]] = ("train", "val", "test")
_HELLO_WORLD_SHA256: Final[str] = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
_PROMOTABLE_REASON: Final[str] = "full_val_test_all_tasks"
_SKILL_FILENAME: Final[str] = "SKILL.md"
_REFERENCES_DIRNAME: Final[str] = "references"
_SKILL_BODY: Final[str] = "# skill"
_GUIDE_BODY: Final[str] = "guide"
_SPLITS_CSV: Final[str] = "train,val"
_INT_DEFAULT: Final[int] = 42
_FLOAT_DEFAULT: Final[float] = 0.5
_STR_DEFAULT: Final[str] = "default"
_OOPAQUE_INT_DEFAULT: Final[int] = 7
_OOPAQUE_STR_DEFAULT: Final[str] = "fallback"
_SAMPLE_INT: Final[int] = 7
_SAMPLE_INT_PARSE: Final[str] = "123"
_SAMPLE_FLOAT_PARSE: Final[str] = "1.25"
_SAMPLE_INT_AS_FLOAT: Final[str] = "5"
_TRUNCATING_FLOAT: Final[float] = 3.7
_TRUNCATED_INT: Final[int] = 3
_PARSED_FLOAT_VALUE: Final[float] = 1.25
_INT_AS_FLOAT_VALUE: Final[float] = 5.0
_SAMPLE_FLOAT_TO_STR: Final[float] = 1.5
_SAMPLE_INT_TO_STR: Final[int] = 42
_RUN_ERROR_DEFAULT_CODE: Final[str] = "run_error"
_RUN_ERROR_CUSTOM_CODE: Final[str] = "boom"
_RUN_ERROR_MESSAGE: Final[str] = "oops"
_FALLBACK_INT: Final[int] = 99
_FALLBACK_FLOAT: Final[float] = 0.5
_INT_PATTERN: Final[str] = r"[+-]?\d+"
_FLOAT_PATTERN: Final[str] = r"[+-]?\d+(?:\.\d+)?"
_NAME_PATTERN: Final[str] = r"[a-z_]+"
_ALPHABET_NON_NUMERIC: Final[str] = "abcdefg"
_MAX_HYPOTHESIS_EXAMPLES: Final[int] = 64
_MAX_SMALL_EXAMPLES: Final[int] = 32
_INT_RANGE: Final[int] = 2**31
_FLOAT_BOUND: Final[float] = 1e6
_MAX_SHORT_TEXT: Final[int] = 16
_HEX_DIGEST_LEN: Final[int] = 64


@beartype
def test_hard_pass_threshold_value() -> None:
    """Verify the test_hard_pass_threshold_value invariant."""
    if _HARD_PASS_THRESHOLD != _EXPECTED_HARD_THRESHOLD:
        pytest.fail(f"expected {_EXPECTED_HARD_THRESHOLD}, got {_HARD_PASS_THRESHOLD}")


@beartype
def test_valid_splits_value() -> None:
    """Verify the test_valid_splits_value invariant."""
    if _VALID_SPLITS != _EXPECTED_VALID_SPLITS:
        pytest.fail(f"expected {_EXPECTED_VALID_SPLITS}, got {_VALID_SPLITS}")


@beartype
def test_forbidden_spec_from_dict_name() -> None:
    """Verify the test_forbidden_spec_from_dict_name invariant."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    if spec.name != "x":
        pytest.fail(f"expected name 'x', got {spec.name!r}")


@beartype
def test_forbidden_spec_from_dict_pattern() -> None:
    """Verify the test_forbidden_spec_from_dict_pattern invariant."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    if spec.pattern.pattern != "y":
        pytest.fail(f"expected pattern 'y', got {spec.pattern.pattern!r}")


@beartype
def test_forbidden_spec_is_frozen() -> None:
    """Verify the test_forbidden_spec_is_frozen invariant."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    with pytest.raises(dataclasses.FrozenInstanceError) as info:
        spec.name = "changed"  # type: ignore[misc]
    match info.value:
        case dataclasses.FrozenInstanceError():
            pass
        case _:
            pytest.fail("expected FrozenInstanceError")


@beartype
def test_candidate_paths_is_frozen(tmp_path: Path) -> None:
    """Verify the test_candidate_paths_is_frozen invariant."""
    paths = CandidatePaths(
        skill=tmp_path / _SKILL_FILENAME, references=tmp_path / _REFERENCES_DIRNAME
    )
    with pytest.raises(dataclasses.FrozenInstanceError) as info:
        paths.skill = tmp_path / "other"  # type: ignore[misc]
    match info.value:
        case dataclasses.FrozenInstanceError():
            pass
        case _:
            pytest.fail("expected FrozenInstanceError")


@beartype
def test_run_error_carries_code() -> None:
    """Verify the test_run_error_carries_code invariant."""
    err = RunError(_RUN_ERROR_MESSAGE, code=_RUN_ERROR_CUSTOM_CODE)
    if err.code != _RUN_ERROR_CUSTOM_CODE:
        pytest.fail(f"expected code {_RUN_ERROR_CUSTOM_CODE}, got {err.code!r}")


@beartype
def test_run_error_default_code() -> None:
    """Verify the test_run_error_default_code invariant."""
    err = RunError(_RUN_ERROR_MESSAGE)
    if err.code != _RUN_ERROR_DEFAULT_CODE:
        pytest.fail(f"expected code {_RUN_ERROR_DEFAULT_CODE}, got {err.code!r}")


@beartype
def test_run_error_string_includes_code() -> None:
    """Verify the test_run_error_string_includes_code invariant."""
    err = RunError(_RUN_ERROR_MESSAGE, code=_RUN_ERROR_CUSTOM_CODE)
    rendered = str(err)
    match rendered:
        case s if _RUN_ERROR_CUSTOM_CODE in s and _RUN_ERROR_MESSAGE in s:
            pass
        case _:
            pytest.fail(f"missing code/message: {rendered}")


@beartype
def test_as_int_none_returns_default() -> None:
    """Verify the test_as_int_none_returns_default invariant."""
    actual = _as_int(None, _INT_DEFAULT)
    if actual != _INT_DEFAULT:
        pytest.fail(f"expected {_INT_DEFAULT}, got {actual}")


@beartype
def test_as_int_int_passthrough() -> None:
    """Verify the test_as_int_int_passthrough invariant."""
    actual = _as_int(_SAMPLE_INT, 0)
    if actual != _SAMPLE_INT:
        pytest.fail(f"expected {_SAMPLE_INT}, got {actual}")


@beartype
def test_as_int_float_truncates() -> None:
    """Verify the test_as_int_float_truncates invariant."""
    actual = _as_int(_TRUNCATING_FLOAT, 0)
    if actual != _TRUNCATED_INT:
        pytest.fail(f"expected {_TRUNCATED_INT}, got {actual}")


@beartype
def test_as_int_str_int() -> None:
    """Verify the test_as_int_str_int invariant."""
    expected = _SAMPLE_INT * 17 + 4
    actual = _as_int(_SAMPLE_INT_PARSE, 0)
    if actual != expected:
        pytest.fail(f"expected {expected}, got {actual}")


@beartype
def test_as_int_str_invalid_returns_default() -> None:
    """Verify the test_as_int_str_invalid_returns_default invariant."""
    actual = _as_int("nope", _FALLBACK_INT)
    if actual != _FALLBACK_INT:
        pytest.fail(f"expected {_FALLBACK_INT}, got {actual}")


@beartype
def test_as_int_bool_true() -> None:
    """Verify the test_as_int_bool_true invariant."""
    actual = _as_int(True, 0)
    if actual != 1:
        pytest.fail(f"expected 1, got {actual}")


@beartype
def test_as_int_bool_false() -> None:
    """Verify the test_as_int_bool_false invariant."""
    actual = _as_int(False, 0)
    if actual != 0:
        pytest.fail(f"expected 0, got {actual}")


@beartype
def test_as_int_object_returns_default() -> None:
    """Verify the test_as_int_object_returns_default invariant."""

    class _Opaque:
        """Opaque class used to test the fallback default of ``_as_int``."""

    actual = _as_int(_Opaque(), _OOPAQUE_INT_DEFAULT)
    if actual != _OOPAQUE_INT_DEFAULT:
        pytest.fail(f"expected {_OOPAQUE_INT_DEFAULT}, got {actual}")


@beartype
def test_as_float_none_returns_default() -> None:
    """Verify the test_as_float_none_returns_default invariant."""
    actual = _as_float(None, _FLOAT_DEFAULT)
    if actual != _FLOAT_DEFAULT:
        pytest.fail(f"expected {_FLOAT_DEFAULT}, got {actual}")


@beartype
def test_as_float_int_passthrough() -> None:
    """Verify the test_as_float_int_passthrough invariant."""
    expected = float(_SAMPLE_INT)
    actual = _as_float(_SAMPLE_INT, 0.0)
    if actual != expected:
        pytest.fail(f"expected {expected}, got {actual}")


@beartype
def test_as_float_str_float() -> None:
    """Verify the test_as_float_str_float invariant."""
    actual = _as_float(_SAMPLE_FLOAT_PARSE, 0.0)
    if actual != _PARSED_FLOAT_VALUE:
        pytest.fail(f"expected {_PARSED_FLOAT_VALUE}, got {actual}")


@beartype
def test_as_float_str_int_parses() -> None:
    """Verify the test_as_float_str_int_parses invariant."""
    actual = _as_float(_SAMPLE_INT_AS_FLOAT, 0.0)
    if actual != _INT_AS_FLOAT_VALUE:
        pytest.fail(f"expected {_INT_AS_FLOAT_VALUE}, got {actual}")


@beartype
def test_as_float_str_invalid_returns_default() -> None:
    """Verify the test_as_float_str_invalid_returns_default invariant."""
    actual = _as_float("nope", _FALLBACK_FLOAT)
    if actual != _FALLBACK_FLOAT:
        pytest.fail(f"expected {_FALLBACK_FLOAT}, got {actual}")


@beartype
def test_as_float_bool_true() -> None:
    """Verify the test_as_float_bool_true invariant."""
    actual = _as_float(True, 0.0)
    if actual != 1.0:
        pytest.fail(f"expected 1.0, got {actual}")


@beartype
def test_as_float_bool_false() -> None:
    """Verify the test_as_float_bool_false invariant."""
    actual = _as_float(False, 0.0)
    if actual != 0.0:
        pytest.fail(f"expected 0.0, got {actual}")


@beartype
def test_as_str_passthrough() -> None:
    """Verify the test_as_str_passthrough invariant."""
    actual = _as_str("hello", _STR_DEFAULT)
    if actual != "hello":
        pytest.fail(f"expected 'hello', got {actual!r}")


@beartype
def test_as_str_int_to_string() -> None:
    """Verify the test_as_str_int_to_string invariant."""
    expected = str(_SAMPLE_INT_TO_STR)
    actual = _as_str(_SAMPLE_INT_TO_STR, _STR_DEFAULT)
    if actual != expected:
        pytest.fail(f"expected {expected!r}, got {actual!r}")


@beartype
def test_as_str_bool_true() -> None:
    """Verify the test_as_str_bool_true invariant."""
    actual = _as_str(True, _STR_DEFAULT)
    if actual != "True":
        pytest.fail(f"expected 'True', got {actual!r}")


@beartype
def test_as_str_bool_false() -> None:
    """Verify the test_as_str_bool_false invariant."""
    actual = _as_str(False, _STR_DEFAULT)
    if actual != "False":
        pytest.fail(f"expected 'False', got {actual!r}")


@beartype
def test_as_str_none_returns_default() -> None:
    """Verify the test_as_str_none_returns_default invariant."""
    actual = _as_str(None, _OOPAQUE_STR_DEFAULT)
    if actual != _OOPAQUE_STR_DEFAULT:
        pytest.fail(f"expected {_OOPAQUE_STR_DEFAULT}, got {actual!r}")


@beartype
def test_as_str_float_to_string() -> None:
    """Verify the test_as_str_float_to_string invariant."""
    expected = str(_SAMPLE_FLOAT_TO_STR)
    actual = _as_str(_SAMPLE_FLOAT_TO_STR, _STR_DEFAULT)
    if actual != expected:
        pytest.fail(f"expected {expected!r}, got {actual!r}")


@beartype
def test_as_str_object_returns_default() -> None:
    """Verify the test_as_str_object_returns_default invariant."""

    class _Opaque:
        """Opaque class used to test the fallback default of ``_as_str``."""

    actual = _as_str(_Opaque(), _OOPAQUE_STR_DEFAULT)
    if actual != _OOPAQUE_STR_DEFAULT:
        pytest.fail(f"expected {_OOPAQUE_STR_DEFAULT}, got {actual!r}")


@beartype
def test_split_values_basic_csv() -> None:
    """Verify the test_split_values_basic_csv invariant."""
    parts = split_values(_SPLITS_CSV)
    expected = ["train", "val"]
    if parts != expected:
        pytest.fail(f"expected {expected}, got {parts}")


@beartype
def test_split_values_empty() -> None:
    """Verify the test_split_values_empty invariant."""
    parts = split_values("")
    if parts:
        pytest.fail(f"expected [], got {parts}")


@beartype
def test_split_values_strips_whitespace() -> None:
    """Verify the test_split_values_strips_whitespace invariant."""
    parts = split_values(" train , val ")
    expected = ["train", "val"]
    if parts != expected:
        pytest.fail(f"expected {expected}, got {parts}")


@beartype
def test_split_values_skips_blank_fields() -> None:
    """Verify the test_split_values_skips_blank_fields invariant."""
    parts = split_values("train,,val,")
    expected = ["train", "val"]
    if parts != expected:
        pytest.fail(f"expected {expected}, got {parts}")


@beartype
def test_split_family_id_csv_pattern() -> None:
    """Verify the test_split_family_id_csv_pattern invariant."""
    actual = split_family_id("repair_csv_case00_alpha")
    if actual != "repair_csv_alpha":
        pytest.fail(f"expected 'repair_csv_alpha', got {actual!r}")


@beartype
def test_split_family_id_summary_pattern() -> None:
    """Verify the test_split_family_id_summary_pattern invariant."""
    actual = split_family_id("repair_summary_case07_beta")
    if actual != "repair_summary_beta":
        pytest.fail(f"expected 'repair_summary_beta', got {actual!r}")


@beartype
def test_split_family_id_perf_folklore() -> None:
    """Verify the test_split_family_id_perf_folklore invariant."""
    actual = split_family_id("review_perf_folklore_four_rayon_smallvec")
    if actual != "review_perf_folklore_rayon_smallvec":
        pytest.fail(f"expected 'review_perf_folklore_rayon_smallvec', got {actual!r}")
    actual = split_family_id("review_perf_folklore_tiny_stdvec_default")
    if actual != "review_perf_folklore_stdvec_default":
        pytest.fail(f"expected 'review_perf_folklore_stdvec_default', got {actual!r}")


@beartype
def test_split_family_id_unknown_returns_itself() -> None:
    """Verify the test_split_family_id_unknown_returns_itself invariant."""
    actual = split_family_id("not_a_real_pattern")
    if actual != "not_a_real_pattern":
        pytest.fail(f"expected 'not_a_real_pattern', got {actual!r}")


@beartype
def test_sha256_file_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the test_sha256_file_deterministic invariant."""
    target = tmp_path / "file.txt"
    monkeypatch.setattr(Path, "read_bytes", lambda _: b"hello world")
    h1 = sha256_file(target)
    h2 = sha256_file(target)
    if h1 != h2:
        pytest.fail(f"expected equal hashes, got {h1} vs {h2}")


@beartype
def test_sha256_file_known_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the test_sha256_file_known_value invariant."""
    target = tmp_path / "file.txt"
    monkeypatch.setattr(Path, "read_bytes", lambda _: b"hello world")
    actual = sha256_file(target)
    if actual != _HELLO_WORLD_SHA256:
        pytest.fail(f"expected {_HELLO_WORLD_SHA256}, got {actual}")


@beartype
def test_bundle_hashes_includes_skill_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the test_bundle_hashes_includes_skill_key invariant."""
    skill_path = tmp_path / _SKILL_FILENAME
    monkeypatch.setattr(Path, "read_bytes", lambda _: _SKILL_BODY.encode())
    hashes: BundleHashesDict = bundle_hashes(tmp_path)
    match hashes:
        case {"skill": skill_hash}:
            expected = sha256_file(skill_path)
            if skill_hash != expected:
                pytest.fail(f"expected {expected}, got {skill_hash}")
        case _:
            pytest.fail("missing skill key")


@beartype
def test_bundle_hashes_includes_references_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify the test_bundle_hashes_includes_references_key invariant."""
    refs = tmp_path / _REFERENCES_DIRNAME
    guide = refs / "guide.md"
    monkeypatch.setattr(Path, "read_bytes", lambda _: _GUIDE_BODY.encode())
    monkeypatch.setattr(Path, "exists", lambda _: True)
    monkeypatch.setattr(Path, "rglob", lambda _, _pattern: iter([guide]))
    monkeypatch.setattr(Path, "is_file", lambda _: True)
    hashes = bundle_hashes(tmp_path)
    match hashes:
        case {"references": refs_hash}:
            if "references/guide.md" not in refs_hash:
                pytest.fail(f"missing 'references/guide.md' in {refs_hash}")
        case _:
            pytest.fail("missing references key")


@beartype
def test_promotion_status_non_promotable_targeted() -> None:
    """Verify the test_promotion_status_non_promotable_targeted invariant."""
    eligible, reason = _promotion_status(["val", "test"], frozenset({"id1"}), "all")
    match (eligible, reason):
        case (False, str()):
            if "targeted_ids_selected" not in reason:
                pytest.fail(f"missing 'targeted_ids_selected' in {reason!r}")
        case _:
            pytest.fail("expected non-promotable with targeted ids")


@beartype
def test_promotion_status_non_promotable_splits() -> None:
    """Verify the test_promotion_status_non_promotable_splits invariant."""
    eligible, reason = _promotion_status(["train"], frozenset(), "all")
    match eligible:
        case False:
            if "splits_must_be_val_test" not in reason:
                pytest.fail(f"missing 'splits_must_be_val_test' in {reason!r}")
        case _:
            pytest.fail("expected non-promotable with wrong splits")


@beartype
def test_promotion_status_non_promotable_kind() -> None:
    """Verify the test_promotion_status_non_promotable_kind invariant."""
    eligible, reason = _promotion_status(["val", "test"], frozenset(), "review")
    match eligible:
        case False:
            if "kind=review" not in reason:
                pytest.fail(f"missing 'kind=review' in {reason!r}")
        case _:
            pytest.fail("expected non-promotable with non-all kind")


@beartype
def test_promotion_status_promotable() -> None:
    """Verify the test_promotion_status_promotable invariant."""
    eligible, reason = _promotion_status(["val", "test"], frozenset(), "all")
    if not eligible:
        pytest.fail("expected eligible=True")
    if reason != _PROMOTABLE_REASON:
        pytest.fail(f"expected reason {_PROMOTABLE_REASON}, got {reason!r}")


@given(name=st.text(min_size=1, max_size=32), pattern=st.from_regex(_NAME_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_forbidden_spec_from_dict_round_trip(name: str, pattern: str) -> None:
    """Verify the test_forbidden_spec_from_dict_round_trip invariant."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name=name, pattern=pattern))
    if spec.name != name:
        pytest.fail(f"expected name {name!r}, got {spec.name!r}")
    if spec.pattern.pattern != pattern:
        pytest.fail(f"expected pattern {pattern!r}, got {spec.pattern.pattern!r}")


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.from_regex(_INT_PATTERN, fullmatch=True),
        st.text(alphabet=_ALPHABET_NON_NUMERIC, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
@beartype
def test_as_int_coerces(value: object) -> None:
    """Verify the test_as_int_coerces invariant."""
    result = _as_int(value, 0)
    match value:
        case bool() | int():
            expected = int(value)
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case float():
            expected = int(value)
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case str() if re.fullmatch(_INT_PATTERN, value):
            expected = int(value)
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case _:
            if result != 0:
                pytest.fail(f"expected 0, got {result}")


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.from_regex(_FLOAT_PATTERN, fullmatch=True),
        st.text(alphabet=_ALPHABET_NON_NUMERIC, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
@beartype
def test_as_float_coerces(value: object) -> None:
    """Verify the test_as_float_coerces invariant."""
    result = _as_float(value, 0.0)
    match value:
        case bool():
            expected = float(int(value))
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case int() | float():
            expected = float(value)
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case str() if re.fullmatch(_FLOAT_PATTERN, value):
            expected = float(value)
            if result != expected:
                pytest.fail(f"expected {expected}, got {result}")
        case _:
            if result != 0.0:
                pytest.fail(f"expected 0.0, got {result}")


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(
            min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False
        ),
        st.text(min_size=1, max_size=_MAX_SHORT_TEXT),
        st.lists(st.integers(), max_size=3),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
@beartype
def test_as_str_coerces(value: object) -> None:
    """Verify the test_as_str_coerces invariant."""
    result = _as_str(value, _STR_DEFAULT)
    match value:
        case str():
            if result != value:
                pytest.fail(f"expected {value!r}, got {result!r}")
        case bool() | int() | float():
            expected = str(value)
            if result != expected:
                pytest.fail(f"expected {expected!r}, got {result!r}")
        case _:
            if result != _STR_DEFAULT:
                pytest.fail(f"expected {_STR_DEFAULT!r}, got {result!r}")


@given(value=st.text(max_size=64))
@settings(
    max_examples=_MAX_HYPOTHESIS_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_split_values_returns_clean_parts(tmp_path: Path, value: str) -> None:
    """Verify the test_split_values_returns_clean_parts invariant."""
    del tmp_path
    parts = split_values(value)
    for part in parts:
        if part != part.strip():
            pytest.fail(f"part not stripped: {part!r}")
        if not part:
            pytest.fail(f"expected non-empty part in {parts!r}")
        if "," in part:
            pytest.fail(f"part contains comma: {part!r}")


# --- @given siblings for example tests below (preserve original tests above) ---


@pytest.mark.property
@given(
    name=st.text(min_size=1, max_size=32),
    pattern=st.from_regex(r"[a-zA-Z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_forbidden_spec_from_dict_name_property(name: str, pattern: str) -> None:
    """Property: ``ForbiddenSpec.from_dict`` always echoes the supplied ``name``."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name=name, pattern=pattern))
    if spec.name != name:
        pytest.fail(f"expected name {name!r}, got {spec.name!r}")


@pytest.mark.property
@given(
    name=st.text(min_size=1, max_size=32),
    pattern=st.from_regex(r"[a-zA-Z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_forbidden_spec_from_dict_pattern_property(name: str, pattern: str) -> None:
    """Property: ``ForbiddenSpec.from_dict`` compiles the pattern into a regex object."""
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name=name, pattern=pattern))
    if spec.pattern.pattern != pattern:
        pytest.fail(f"expected pattern {pattern!r}, got {spec.pattern.pattern!r}")


@pytest.mark.property
@given(
    message=st.text(min_size=0, max_size=32),
    code=st.from_regex(r"[a-z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_run_error_carries_code_property(message: str, code: str) -> None:
    """Property: ``RunError`` always preserves the supplied ``code``."""
    err = RunError(message, code=code)
    if err.code != code:
        pytest.fail(f"expected code {code!r}, got {err.code!r}")


@pytest.mark.property
@given(message=st.text(min_size=0, max_size=32))
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_run_error_default_code_property(message: str) -> None:
    """Property: ``RunError`` without a code uses ``'run_error'`` as the default."""
    err = RunError(message)
    if err.code != _RUN_ERROR_DEFAULT_CODE:
        pytest.fail(f"expected code {_RUN_ERROR_DEFAULT_CODE!r}, got {err.code!r}")


@pytest.mark.property
@given(
    message=st.text(min_size=1, max_size=32),
    code=st.from_regex(r"[a-z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_run_error_string_includes_code_property(message: str, code: str) -> None:
    """Property: ``str(RunError)`` always contains both the code and the message."""
    err = RunError(message, code=code)
    rendered = str(err)
    if code not in rendered or message not in rendered:
        pytest.fail(f"missing code/message in {rendered!r}")


@pytest.mark.property
@given(
    domain=st.sampled_from(["case00", "case05", "case10", "case19"]),
    suffix=st.from_regex(r"[a-z][a-z_]+[a-z]", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_csv_pattern_property(domain: str, suffix: str) -> None:
    """Property: ``split_family_id`` reduces the ``repair_csv_<domain>_<suffix>`` family."""
    task_id = f"repair_csv_{domain}_{suffix}"
    expected = f"repair_csv_{suffix}"
    actual = split_family_id(task_id)
    if actual != expected:
        pytest.fail(f"expected {expected!r}, got {actual!r}")


@pytest.mark.property
@given(
    domain=st.sampled_from(["case00", "case05", "case10", "case19"]),
    suffix=st.from_regex(r"[a-z][a-z_]+[a-z]", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_summary_pattern_property(domain: str, suffix: str) -> None:
    """Property: ``split_family_id`` reduces the ``repair_summary_<domain>_<suffix>`` family."""
    task_id = f"repair_summary_{domain}_{suffix}"
    expected = f"repair_summary_{suffix}"
    actual = split_family_id(task_id)
    if actual != expected:
        pytest.fail(f"expected {expected!r}, got {actual!r}")


@pytest.mark.property
@given(
    size=st.sampled_from(["four", "tiny", "small", "fixed"]),
    suffix=st.from_regex(r"[a-z_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_perf_folklore_property(size: str, suffix: str) -> None:
    """Property: ``split_family_id`` reduces ``review_perf_folklore_<size>_<suffix>``."""
    task_id = f"review_perf_folklore_{size}_{suffix}"
    expected = f"review_perf_folklore_{suffix}"
    actual = split_family_id(task_id)
    if actual != expected:
        pytest.fail(f"expected {expected!r}, got {actual!r}")


@pytest.mark.property
@given(task_id=st.text(min_size=1, max_size=64))
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_split_family_id_unknown_returns_itself_property(task_id: str) -> None:
    """Property: ``split_family_id`` returns the input unchanged for non-matching ids."""
    actual = split_family_id(task_id)
    if actual != task_id:
        pytest.fail(f"expected {task_id!r}, got {actual!r}")


@pytest.mark.property
@given(payload=st.binary(min_size=0, max_size=32))
@settings(
    max_examples=_MAX_SMALL_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_sha256_file_deterministic_property(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    """Property: ``sha256_file`` is deterministic for any payload."""
    monkeypatch.setattr(Path, "read_bytes", lambda _: payload)
    target = tmp_path / "blob.bin"
    first = sha256_file(target)
    second = sha256_file(target)
    if first != second:
        pytest.fail(f"non-deterministic: {first} vs {second}")


@pytest.mark.property
@given(payload=st.binary(min_size=0, max_size=32))
@settings(
    max_examples=_MAX_SMALL_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_sha256_file_matches_hashlib_property(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    """Property: ``sha256_file`` matches ``hashlib.sha256(payload).hexdigest()``."""
    monkeypatch.setattr(Path, "read_bytes", lambda _: payload)
    target = tmp_path / "blob.bin"
    actual = sha256_file(target)
    expected = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        pytest.fail(f"expected {expected}, got {actual}")


@pytest.mark.property
@given(body=st.text(min_size=0, max_size=32))
@settings(
    max_examples=_MAX_SMALL_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_bundle_hashes_includes_skill_key_property(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    """Property: ``bundle_hashes`` always includes the 64-char ``skill`` digest."""
    _ = tmp_path / _SKILL_FILENAME
    monkeypatch.setattr(Path, "read_bytes", lambda _: body.encode())
    hashes: BundleHashesDict = bundle_hashes(tmp_path)
    skill_hash = hashes["skill"]
    if len(skill_hash) != _HEX_DIGEST_LEN:
        pytest.fail(f"expected 64-char digest, got {skill_hash!r}")


@pytest.mark.property
@given(
    ref_body=st.text(min_size=1, max_size=32),
    ref_name=st.from_regex(r"[a-z][a-z_]+\.md", fullmatch=True),
)
@settings(
    max_examples=_MAX_SMALL_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@beartype
def test_bundle_hashes_includes_references_key_property(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ref_body: str,
    ref_name: str,
) -> None:
    """Property: ``bundle_hashes`` always emits a path under ``references/`` for each ref."""
    refs_dir = tmp_path / _REFERENCES_DIRNAME
    guide = refs_dir / ref_name
    monkeypatch.setattr(Path, "read_bytes", lambda _: ref_body.encode())
    monkeypatch.setattr(Path, "exists", lambda _: True)
    monkeypatch.setattr(Path, "rglob", lambda _, _pattern: iter([guide]))
    monkeypatch.setattr(Path, "is_file", lambda _: True)
    hashes = bundle_hashes(tmp_path)
    refs_hash = hashes["references"]
    expected_key = f"references/{ref_name}"
    if expected_key not in refs_hash:
        pytest.fail(f"missing {expected_key!r} in {refs_hash!r}")


@pytest.mark.property
@given(
    targeted_id=st.from_regex(r"[a-z0-9_]+", fullmatch=True),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_non_promotable_targeted_property(targeted_id: str) -> None:
    """Property: any non-empty ids set disables promotion."""
    eligible, reason = _promotion_status(["val", "test"], frozenset({targeted_id}), "all")
    if eligible:
        pytest.fail("expected non-promotable with targeted ids")
    if "targeted_ids_selected" not in reason:
        pytest.fail(f"missing 'targeted_ids_selected' in {reason!r}")


@pytest.mark.property
@given(
    other_split=st.sampled_from(["train"]),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_non_promotable_splits_property(other_split: str) -> None:
    """Property: any splits other than exactly ``(val, test)`` is non-promotable."""
    splits = (other_split,)
    eligible, reason = _promotion_status(splits, frozenset(), "all")
    if eligible:
        pytest.fail(f"expected non-promotable for splits={splits!r}")
    if "splits_must_be_val_test" not in reason:
        pytest.fail(f"missing 'splits_must_be_val_test' in {reason!r}")


@pytest.mark.property
@given(
    kind=st.sampled_from(["review", "repair"]),
)
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
@beartype
def test_promotion_status_non_promotable_kind_property(kind: str) -> None:
    """Property: kind other than ``all`` is non-promotable."""
    eligible, reason = _promotion_status(["val", "test"], frozenset(), kind)
    if eligible:
        pytest.fail(f"expected non-promotable for kind={kind}")
    if f"kind={kind}" not in reason:
        pytest.fail(f"missing 'kind={kind}' in {reason!r}")


@beartype
def test_promotion_status_promotable_property() -> None:
    """Property: ``(val, test)`` + empty ids + ``kind='all'`` is promotable."""
    eligible, reason = _promotion_status(["val", "test"], frozenset(), "all")
    if not eligible:
        pytest.fail("expected eligible=True")
    if reason != _PROMOTABLE_REASON:
        pytest.fail(f"expected reason {_PROMOTABLE_REASON}, got {reason!r}")
