from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from skillopt_train.skill import REQUIRED_FILES, Skill

_SKILLS_ROOT: Final[Path] = Path("skills")
_SKILL_BODY: Final[str] = "# {name}\n\nbaseline skill bundle\n"
_PROMPT_BODY: Final[str] = "PROMPT {name}\n"
_TASKS_BODY: Final[str] = '{"id": "t1"}\n'
_EVAL_BODY: Final[str] = (
    "def run_eval(candidate, tasks, run_root):\n"
    "    return {}\n"
)


def _make_skill(
    root: Path,
    name: str,
    *,
    forbidden: tuple[str, ...] = ("unwrap",),
    eval_body: str = _EVAL_BODY,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        _SKILL_BODY.format(name=name), encoding="utf-8"
    )
    rubric_payload: dict[str, object] = {
        "name": name,
        "description": "test rubric",
        "forbidden_tokens": {tok: f"forbidden:{tok}" for tok in forbidden},
        "grade_issue_keys": ["json_errors"],
        "grade_returncode_keys": ["cargo_fmt_returncode"],
        "success_threshold_hard": 1.0,
        "max_examples": 5,
    }
    (skill_dir / "rubric.json").write_text(
        json.dumps(rubric_payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (skill_dir / "prompt.md").write_text(
        _PROMPT_BODY.format(name=name), encoding="utf-8",
    )
    (skill_dir / "tasks.jsonl").write_text(_TASKS_BODY, encoding="utf-8")
    (skill_dir / "eval.py").write_text(eval_body, encoding="utf-8")
    return skill_dir


@pytest.fixture
def skills_root(tmp_path: Path) -> Iterator[Path]:
    _make_skill(tmp_path, "alpha")
    _make_skill(tmp_path, "beta")
    yield tmp_path


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_skill_discover_finds_holzman_rust() -> None:
    skills = Skill.discover(_SKILLS_ROOT)
    names = {s.name for s in skills}
    assert "holzman-rust" in names


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_skill_find_holzman_rust() -> None:
    skill = Skill.find(_SKILLS_ROOT, "holzman-rust")
    assert skill.name == "holzman-rust"
    assert skill.rubric.name == "holzman-rust"


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_skill_find_react_typescript() -> None:
    skill = Skill.find(_SKILLS_ROOT, "react-typescript")
    assert skill.name == "react-typescript"
    assert skill.rubric.name == "react-typescript"


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_holzman_rust_rubric_has_unwrap() -> None:
    skill = Skill.find(_SKILLS_ROOT, "holzman-rust")
    assert skill.rubric.forbidden_tokens["unwrap"] == "forbidden:unwrap"


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_react_typescript_rubric_has_any() -> None:
    skill = Skill.find(_SKILLS_ROOT, "react-typescript")
    assert skill.rubric.forbidden_tokens["any"] == "forbidden:any"


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_holzman_rust_prompt_has_placeholders() -> None:
    skill = Skill.find(_SKILLS_ROOT, "holzman-rust")
    prompt = skill.load_prompt()
    for placeholder in ("{skill_md}", "{critique}", "{previous_addendum}"):
        assert placeholder in prompt, f"missing placeholder {placeholder!r}"


@pytest.mark.skipif(
    not _SKILLS_ROOT.is_dir(),
    reason="skills/ directory not present in this environment",
)
def test_react_typescript_prompt_has_placeholders() -> None:
    skill = Skill.find(_SKILLS_ROOT, "react-typescript")
    prompt = skill.load_prompt()
    for placeholder in ("{skill_md}", "{critique}", "{previous_addendum}"):
        assert placeholder in prompt, f"missing placeholder {placeholder!r}"


def test_skill_discover_finds_skills_in_root(skills_root: Path) -> None:
    found = Skill.discover(skills_root)
    assert [s.name for s in found] == ["alpha", "beta"]


def test_skill_find_raises_for_missing_skill(skills_root: Path) -> None:
    from skillopt_train.errors import ConfigError

    with pytest.raises(ConfigError) as info:
        Skill.find(skills_root, "missing")
    assert info.value.code == "skill_not_found"


def test_required_files_constant_matches_spec() -> None:
    assert REQUIRED_FILES == ("SKILL.md", "rubric.json", "prompt.md", "tasks.jsonl")


from typing import Final  # noqa: E402
