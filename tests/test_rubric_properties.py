from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from scripts.generate_holzman_rust_dataset import (
    ForbiddenPattern,
    ForbiddenSpec,
    split_family_id,
)
from scripts.run_holzman_candidate_eval import (
    BundleHashesDict,
    CandidatePaths,
    RunError,
    _HARD_PASS_THRESHOLD,
    _VALID_SPLITS,
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
_HELLO_WORLD_SHA256: Final[str] = (
    "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
)
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


def test_hard_pass_threshold_value() -> None:
    assert _HARD_PASS_THRESHOLD == _EXPECTED_HARD_THRESHOLD


def test_valid_splits_value() -> None:
    assert _VALID_SPLITS == _EXPECTED_VALID_SPLITS


def test_forbidden_spec_from_dict_name() -> None:
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    assert spec.name == "x"


def test_forbidden_spec_from_dict_pattern() -> None:
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    assert spec.pattern.pattern == "y"


def test_forbidden_spec_is_frozen() -> None:
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name="x", pattern="y"))
    with pytest.raises(dataclasses.FrozenInstanceError) as info:
        spec.name = "changed"  # type: ignore[misc]
    match info.value:
        case dataclasses.FrozenInstanceError():
            pass
        case _:
            pytest.fail("expected FrozenInstanceError")


def test_candidate_paths_is_frozen(tmp_path: Path) -> None:
    paths = CandidatePaths(skill=tmp_path / _SKILL_FILENAME, references=tmp_path / _REFERENCES_DIRNAME)
    with pytest.raises(dataclasses.FrozenInstanceError) as info:
        paths.skill = tmp_path / "other"  # type: ignore[misc]
    match info.value:
        case dataclasses.FrozenInstanceError():
            pass
        case _:
            pytest.fail("expected FrozenInstanceError")


def test_run_error_carries_code() -> None:
    err = RunError(_RUN_ERROR_MESSAGE, code=_RUN_ERROR_CUSTOM_CODE)
    assert err.code == _RUN_ERROR_CUSTOM_CODE


def test_run_error_default_code() -> None:
    err = RunError(_RUN_ERROR_MESSAGE)
    assert err.code == _RUN_ERROR_DEFAULT_CODE


def test_run_error_string_includes_code() -> None:
    err = RunError(_RUN_ERROR_MESSAGE, code=_RUN_ERROR_CUSTOM_CODE)
    rendered = str(err)
    match rendered:
        case s if _RUN_ERROR_CUSTOM_CODE in s and _RUN_ERROR_MESSAGE in s:
            pass
        case _:
            pytest.fail(f"missing code/message: {rendered}")


def test_as_int_none_returns_default() -> None:
    assert _as_int(None, _INT_DEFAULT) == _INT_DEFAULT


def test_as_int_int_passthrough() -> None:
    assert _as_int(_SAMPLE_INT, 0) == _SAMPLE_INT


def test_as_int_float_truncates() -> None:
    assert _as_int(_TRUNCATING_FLOAT, 0) == 3


def test_as_int_str_int() -> None:
    assert _as_int(_SAMPLE_INT_PARSE, 0) == _SAMPLE_INT * 17 + 4


def test_as_int_str_invalid_returns_default() -> None:
    assert _as_int("nope", _FALLBACK_INT) == _FALLBACK_INT


def test_as_int_bool_true() -> None:
    assert _as_int(True, 0) == 1


def test_as_int_bool_false() -> None:
    assert _as_int(False, 0) == 0


def test_as_int_object_returns_default() -> None:
    class _Opaque:
        pass

    assert _as_int(_Opaque(), _OOPAQUE_INT_DEFAULT) == _OOPAQUE_INT_DEFAULT


def test_as_float_none_returns_default() -> None:
    assert _as_float(None, _FLOAT_DEFAULT) == _FLOAT_DEFAULT


def test_as_float_int_passthrough() -> None:
    assert _as_float(_SAMPLE_INT, 0.0) == float(_SAMPLE_INT)


def test_as_float_str_float() -> None:
    assert _as_float(_SAMPLE_FLOAT_PARSE, 0.0) == 1.25


def test_as_float_str_int_parses() -> None:
    assert _as_float(_SAMPLE_INT_AS_FLOAT, 0.0) == 5.0


def test_as_float_str_invalid_returns_default() -> None:
    assert _as_float("nope", _FALLBACK_FLOAT) == _FALLBACK_FLOAT


def test_as_float_bool_true() -> None:
    assert _as_float(True, 0.0) == 1.0


def test_as_float_bool_false() -> None:
    assert _as_float(False, 0.0) == 0.0


def test_as_str_passthrough() -> None:
    assert _as_str("hello", _STR_DEFAULT) == "hello"


def test_as_str_int_to_string() -> None:
    assert _as_str(_SAMPLE_INT_TO_STR, _STR_DEFAULT) == str(_SAMPLE_INT_TO_STR)


def test_as_str_bool_true() -> None:
    assert _as_str(True, _STR_DEFAULT) == "True"


def test_as_str_bool_false() -> None:
    assert _as_str(False, _STR_DEFAULT) == "False"


def test_as_str_none_returns_default() -> None:
    assert _as_str(None, _OOPAQUE_STR_DEFAULT) == _OOPAQUE_STR_DEFAULT


def test_as_str_float_to_string() -> None:
    assert _as_str(_SAMPLE_FLOAT_TO_STR, _STR_DEFAULT) == str(_SAMPLE_FLOAT_TO_STR)


def test_as_str_object_returns_default() -> None:
    class _Opaque:
        pass

    assert _as_str(_Opaque(), _OOPAQUE_STR_DEFAULT) == _OOPAQUE_STR_DEFAULT


def test_split_values_basic_csv() -> None:
    assert split_values(_SPLITS_CSV) == ["train", "val"]


def test_split_values_empty() -> None:
    assert split_values("") == []


def test_split_values_strips_whitespace() -> None:
    assert split_values(" train , val ") == ["train", "val"]


def test_split_values_skips_blank_fields() -> None:
    assert split_values("train,,val,") == ["train", "val"]


def test_split_family_id_csv_pattern() -> None:
    assert split_family_id("repair_csv_case00_alpha") == "repair_csv_alpha"


def test_split_family_id_summary_pattern() -> None:
    assert split_family_id("repair_summary_case07_beta") == "repair_summary_beta"


def test_split_family_id_perf_folklore() -> None:
    assert split_family_id("review_perf_folklore_four_rayon_smallvec") == "review_perf_folklore_rayon_smallvec"
    assert split_family_id("review_perf_folklore_tiny_stdvec_default") == "review_perf_folklore_stdvec_default"


def test_split_family_id_unknown_returns_itself() -> None:
    assert split_family_id("not_a_real_pattern") == "not_a_real_pattern"


def test_sha256_file_deterministic(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("hello world", encoding="utf-8")
    assert sha256_file(target) == sha256_file(target)


def test_sha256_file_known_value(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("hello world", encoding="utf-8")
    assert sha256_file(target) == _HELLO_WORLD_SHA256


def test_bundle_hashes_includes_skill_key(tmp_path: Path) -> None:
    (tmp_path / _SKILL_FILENAME).write_text(_SKILL_BODY, encoding="utf-8")
    hashes: BundleHashesDict = bundle_hashes(tmp_path)
    match hashes:
        case {"skill": skill_hash}:
            assert skill_hash == sha256_file(tmp_path / _SKILL_FILENAME)
        case _:
            pytest.fail("missing skill key")


def test_bundle_hashes_includes_references_key(tmp_path: Path) -> None:
    (tmp_path / _SKILL_FILENAME).write_text(_SKILL_BODY, encoding="utf-8")
    refs = tmp_path / _REFERENCES_DIRNAME
    refs.mkdir()
    (refs / "guide.md").write_text(_GUIDE_BODY, encoding="utf-8")
    hashes = bundle_hashes(tmp_path)
    match hashes:
        case {"references": refs_hash}:
            assert "references/guide.md" in refs_hash
        case _:
            pytest.fail("missing references key")


def test_promotion_status_non_promotable_targeted() -> None:
    eligible, reason = _promotion_status(["val", "test"], {"id1"}, "all")
    match (eligible, reason):
        case (False, str()):
            assert "targeted_ids_selected" in reason
        case _:
            pytest.fail("expected non-promotable with targeted ids")


def test_promotion_status_non_promotable_splits() -> None:
    eligible, reason = _promotion_status(["train"], set(), "all")
    match eligible:
        case False:
            assert "splits_must_be_val_test" in reason
        case _:
            pytest.fail("expected non-promotable with wrong splits")


def test_promotion_status_non_promotable_kind() -> None:
    eligible, reason = _promotion_status(["val", "test"], set(), "review")
    match eligible:
        case False:
            assert "kind=review" in reason
        case _:
            pytest.fail("expected non-promotable with non-all kind")


def test_promotion_status_promotable() -> None:
    eligible, reason = _promotion_status(["val", "test"], set(), "all")
    assert eligible is True
    assert reason == _PROMOTABLE_REASON


@given(name=st.text(min_size=1, max_size=32), pattern=st.from_regex(_NAME_PATTERN, fullmatch=True))
@settings(max_examples=_MAX_SMALL_EXAMPLES, deadline=None)
def test_forbidden_spec_from_dict_round_trip(name: str, pattern: str) -> None:
    spec = ForbiddenSpec.from_dict(ForbiddenPattern(name=name, pattern=pattern))
    assert spec.name == name
    assert spec.pattern.pattern == pattern


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False),
        st.from_regex(_INT_PATTERN, fullmatch=True),
        st.text(alphabet=_ALPHABET_NON_NUMERIC, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
def test_as_int_coerces(value: object) -> None:
    result = _as_int(value, 0)
    match value:
        case bool() | int():
            assert result == int(value)
        case float():
            assert result == int(value)
        case str() as s if re.fullmatch(_INT_PATTERN, s):
            assert result == int(s)
        case _:
            assert result == 0


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False),
        st.from_regex(_FLOAT_PATTERN, fullmatch=True),
        st.text(alphabet=_ALPHABET_NON_NUMERIC, min_size=1, max_size=8),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
def test_as_float_coerces(value: object) -> None:
    result = _as_float(value, 0.0)
    match value:
        case bool():
            assert result == float(int(value))
        case int() | float():
            assert result == float(value)
        case str() as s if re.fullmatch(_FLOAT_PATTERN, s):
            assert result == float(s)
        case _:
            assert result == 0.0


@given(
    value=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-_INT_RANGE, max_value=_INT_RANGE),
        st.floats(min_value=-_FLOAT_BOUND, max_value=_FLOAT_BOUND, allow_nan=False, allow_infinity=False),
        st.text(min_size=1, max_size=_MAX_SHORT_TEXT),
        st.lists(st.integers(), max_size=3),
    )
)
@settings(max_examples=_MAX_HYPOTHESIS_EXAMPLES, deadline=None)
def test_as_str_coerces(value: object) -> None:
    result = _as_str(value, _STR_DEFAULT)
    match value:
        case str() as s:
            assert result == s
        case bool() | int() | float():
            assert result == str(value)
        case _:
            assert result == _STR_DEFAULT


@given(value=st.text(max_size=64))
@settings(
    max_examples=_MAX_HYPOTHESIS_EXAMPLES,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_split_values_returns_clean_parts(tmp_path: Path, value: str) -> None:
    del tmp_path
    parts = split_values(value)
    for part in parts:
        assert part == part.strip()
        assert part
        assert "," not in part
