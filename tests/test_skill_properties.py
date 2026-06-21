from __future__ import annotations

import json
import re
import string
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from skillopt_train.errors import ConfigError
from skillopt_train.rubric import Rubric
from skillopt_train.skill import REQUIRED_FILES, Skill

_SKILL_NAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$"
)
_FORBIDDEN_KEYS: Final[tuple[str, ...]] = (
    "unwrap",
    "expect",
    "panic",
    "unsafe",
    "todo",
    "any",
    "as_ref",
)
_FORBIDDEN_VALUES: Final[tuple[str, ...]] = (
    "forbidden:unwrap",
    "forbidden:expect",
    "forbidden:panic",
    "forbidden:unsafe",
    "forbidden:todo",
    "msg",
)
_ISSUE_KEYS: Final[tuple[str, ...]] = (
    "json_errors",
    "mutation_errors",
    "forbidden_matches",
)
_RETURNCODE_KEYS: Final[tuple[str, ...]] = (
    "cargo_fmt_returncode",
    "cargo_clippy_returncode",
    "tsc_returncode",
)
_RUBRIC_NAMES: Final[tuple[str, ...]] = (
    "default",
    "test",
    "custom",
    "alpha",
)
_DESCRIPTIONS: Final[tuple[str, ...]] = (
    "",
    "test rubric",
    "longer description here",
)
_EXAMPLE_COUNT: Final[int] = 30
_FIRST_CHAR_ALPHABET: Final[str] = string.ascii_letters + string.digits
_REST_ALPHABET: Final[str] = string.ascii_letters + string.digits + "_.-"
_TASKS_BODY: Final[str] = '{"id": "t1"}\n'
_INVALID_NAMES: Final[tuple[str, ...]] = (
    "invalid/name",
    "name with space",
    "",
    "..",
    "name!",
    "/leading",
)


def _default_rubric_data(name: str) -> dict[str, object]:
    return {
        "name": name,
        "description": "",
        "forbidden_tokens": {},
        "grade_issue_keys": [],
        "grade_returncode_keys": [],
        "success_threshold_hard": 1.0,
        "max_examples": 5,
    }


def _make_skill_dir(
    parent: Path,
    name: str,
    *,
    rubric_data: dict[str, object] | None = None,
    write_eval: bool = True,
    omit_files: frozenset[str] = frozenset(),
) -> Path:
    skill_dir = parent / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    if "SKILL.md" not in omit_files:
        (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    if "rubric.json" not in omit_files:
        payload = _default_rubric_data(name) if rubric_data is None else rubric_data
        (skill_dir / "rubric.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
    if "prompt.md" not in omit_files:
        (skill_dir / "prompt.md").write_text(f"prompt {name}\n", encoding="utf-8")
    if "tasks.jsonl" not in omit_files:
        (skill_dir / "tasks.jsonl").write_text(_TASKS_BODY, encoding="utf-8")
    if write_eval:
        (skill_dir / "eval.py").write_text("# stub\n", encoding="utf-8")
    return skill_dir


@st.composite
def _rubric_mapping(draw: Any) -> dict[str, object]:
    forbidden_raw = draw(
        st.dictionaries(
            st.sampled_from(_FORBIDDEN_KEYS),
            st.sampled_from(_FORBIDDEN_VALUES),
            min_size=0,
            max_size=5,
        )
    )
    return {
        "name": draw(st.sampled_from(_RUBRIC_NAMES)),
        "description": draw(st.sampled_from(_DESCRIPTIONS)),
        "forbidden_tokens": forbidden_raw,
        "grade_issue_keys": draw(
            st.lists(st.sampled_from(_ISSUE_KEYS), max_size=3)
        ),
        "grade_returncode_keys": draw(
            st.lists(st.sampled_from(_RETURNCODE_KEYS), max_size=3)
        ),
        "success_threshold_hard": draw(
            st.floats(
                min_value=0.0,
                max_value=1.0,
                allow_nan=False,
                allow_infinity=False,
            )
        ),
        "max_examples": draw(st.integers(min_value=1, max_value=20)),
    }


@st.composite
def _skill_name(draw: Any) -> str:
    first = draw(st.sampled_from(_FIRST_CHAR_ALPHABET))
    rest = draw(st.text(alphabet=_REST_ALPHABET, max_size=15))
    return first + rest


@st.composite
def _skill_names(draw: Any, *, min_size: int, max_size: int) -> tuple[str, ...]:
    names = draw(
        st.lists(
            _skill_name(),
            min_size=min_size,
            max_size=max_size,
            unique=True,
        )
    )
    return tuple(names)


@st.composite
def _two_distinct_names(draw: Any) -> tuple[str, str]:
    first = draw(_skill_name())
    second = draw(_skill_name().filter(lambda n: n != first))
    return first, second


@pytest.mark.property
def test_rubric_default_invariants() -> None:
    rubric = Rubric.default()
    assert rubric.forbidden_tokens == {}
    assert rubric.max_examples > 0
    assert rubric.success_threshold_hard == 1.0


@pytest.mark.property
def test_rubric_empty_mapping_returns_valid_rubric() -> None:
    rubric = Rubric.from_mapping({})
    assert rubric.name == "default"
    assert rubric.description == ""
    assert rubric.forbidden_tokens == {}
    assert tuple(rubric.grade_issue_keys) == ()
    assert tuple(rubric.grade_returncode_keys) == ()
    assert rubric.success_threshold_hard == 1.0
    assert rubric.max_examples > 0


@pytest.mark.property
@given(payload=_rubric_mapping())
@settings(max_examples=_EXAMPLE_COUNT)
def test_rubric_round_trip(payload: dict[str, object]) -> None:
    rubric = Rubric.from_mapping(payload)
    rebuilt = Rubric.from_mapping(rubric.to_mapping())
    assert rebuilt.name == rubric.name
    assert rebuilt.description == rubric.description
    assert dict(rebuilt.forbidden_tokens) == dict(rubric.forbidden_tokens)
    assert tuple(rebuilt.grade_issue_keys) == tuple(rubric.grade_issue_keys)
    assert tuple(rebuilt.grade_returncode_keys) == tuple(rubric.grade_returncode_keys)
    assert rebuilt.success_threshold_hard == rubric.success_threshold_hard
    assert rebuilt.max_examples == rubric.max_examples


@pytest.mark.property
@given(payload=_rubric_mapping())
@settings(max_examples=_EXAMPLE_COUNT)
def test_rubric_forbidden_tokens_are_strings(payload: dict[str, object]) -> None:
    rubric = Rubric.from_mapping(payload)
    for key, value in rubric.forbidden_tokens.items():
        assert isinstance(key, str)
        assert isinstance(value, str)


@pytest.mark.property
@given(payload=_rubric_mapping())
@settings(max_examples=_EXAMPLE_COUNT)
def test_rubric_grade_keys_are_strings(payload: dict[str, object]) -> None:
    rubric = Rubric.from_mapping(payload)
    for key in rubric.grade_issue_keys:
        assert isinstance(key, str)
    for key in rubric.grade_returncode_keys:
        assert isinstance(key, str)


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_skill_name_matches_directory(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("skill-name")
    _make_skill_dir(root, name)
    skill = Skill.from_path(root / name)
    assert skill.name == name
    assert skill.path.name == name


@pytest.mark.property
@given(missing=st.sampled_from(REQUIRED_FILES))
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_skill_from_path_missing_required_file(
    tmp_path_factory: pytest.TempPathFactory,
    missing: str,
) -> None:
    root = tmp_path_factory.mktemp("missing-required")
    _make_skill_dir(root, "skill", omit_files=frozenset({missing}))
    with pytest.raises(ConfigError) as info:
        Skill.from_path(root / "skill")
    assert info.value.code == "skill_incomplete"


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_skill_from_path_missing_eval(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("missing-eval")
    _make_skill_dir(root, name, write_eval=False)
    with pytest.raises(ConfigError) as info:
        Skill.from_path(root / name)
    assert info.value.code == "skill_no_eval"


@pytest.mark.property
@given(names=_two_distinct_names())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_discover_skips_invalid(
    tmp_path_factory: pytest.TempPathFactory,
    names: tuple[str, str],
) -> None:
    good_name, bad_name = names
    root = tmp_path_factory.mktemp("discover-invalid")
    _make_skill_dir(root, good_name)
    _make_skill_dir(root, bad_name, omit_files=frozenset({"SKILL.md"}))
    found_names = [s.name for s in Skill.discover(root)]
    assert good_name in found_names
    assert bad_name not in found_names


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_discover_skips_hidden(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("discover-hidden")
    _make_skill_dir(root, name)
    _make_skill_dir(root, f".{name}")
    found_names = [s.name for s in Skill.discover(root)]
    assert name in found_names
    assert f".{name}" not in found_names


@pytest.mark.property
@given(names=_skill_names(min_size=2, max_size=6))
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_discover_sorted(
    tmp_path_factory: pytest.TempPathFactory,
    names: tuple[str, ...],
) -> None:
    root = tmp_path_factory.mktemp("discover-sorted")
    for name in names:
        _make_skill_dir(root, name)
    found_names = [s.name for s in Skill.discover(root)]
    assert found_names == sorted(found_names)
    assert set(found_names) == set(names)


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_find_by_name(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("find-by-name")
    _make_skill_dir(root, name)
    skill = Skill.find(root, name)
    assert skill.name == name
    assert skill.path == root / name


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_find_raises_for_missing(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("find-missing")
    with pytest.raises(ConfigError) as info:
        Skill.find(root, name)
    assert info.value.code == "skill_not_found"


@pytest.mark.property
@given(bad_name=st.sampled_from(_INVALID_NAMES))
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_find_validates_name(
    tmp_path_factory: pytest.TempPathFactory,
    bad_name: str,
) -> None:
    root = tmp_path_factory.mktemp("find-invalid")
    with pytest.raises(ConfigError) as info:
        Skill.find(root, bad_name)
    assert info.value.code == "skill_name_invalid"


_PROMPT_CONTENT: Any = st.text(
    alphabet=st.characters(
        blacklist_characters="\r\n",
        blacklist_categories=("Cs",),
    ),
    max_size=200,
)


@pytest.mark.property
@given(name=_skill_name(), content=_PROMPT_CONTENT)
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_load_prompt_matches_file(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
    content: str,
) -> None:
    root = tmp_path_factory.mktemp("load-prompt")
    _make_skill_dir(root, name)
    (root / name / "prompt.md").write_text(content, encoding="utf-8")
    skill = Skill.from_path(root / name)
    assert skill.load_prompt() == content


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_load_default_config_is_dict(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("load-config")
    _make_skill_dir(root, name)
    skill = Skill.from_path(root / name)
    config = skill.load_default_config()
    assert isinstance(config, Mapping)


@pytest.mark.property
@given(name=_skill_name())
@settings(
    max_examples=_EXAMPLE_COUNT,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_load_default_config_empty_when_no_config(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
) -> None:
    root = tmp_path_factory.mktemp("load-config-empty")
    _make_skill_dir(root, name)
    skill = Skill.from_path(root / name)
    assert skill.config_path is None
    assert skill.load_default_config() == {}