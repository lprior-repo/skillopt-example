from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

from skillopt_train.errors import MutatorError
from skillopt_train.mutator import Mutator, MutatorMeta, propose
from skillopt_train.providers import (
    MockProvider,
    ScriptedTurn,
    make_json_response,
)

_SAFE_ADDENDUM: Final[str] = "first addendum body\n"
_SAFE_ADDENDUM_TWO: Final[str] = "second addendum body\n"
_LONG_ADDENDUM_CHARS: Final[int] = 500
_MAX_ADDENDUM_CHARS: Final[int] = 100


def _setup_dirs(tmp_path: Path) -> tuple[Path, Path, Path]:
    skill_root = tmp_path / "skill"
    candidate_root = tmp_path / "candidates"
    base_overlay = tmp_path / "overlay"
    skill_root.mkdir()
    base_overlay.mkdir()
    (skill_root / "SKILL.md").write_text("# base skill\n", encoding="utf-8")
    return skill_root, candidate_root, base_overlay


def _scripted(provider: MockProvider, payload: Mapping[str, object]) -> None:
    provider.script(ScriptedTurn(match="", response=make_json_response(payload)))


def test_propose_writes_addendum_file(tmp_path: Path) -> None:
    skill_root, candidate_root, base_overlay = _setup_dirs(tmp_path)
    provider = MockProvider()
    _scripted(provider, {"addendum": _SAFE_ADDENDUM, "reasoning": "ok"})
    overlay, meta = propose(
        provider=provider,
        skill_root=skill_root,
        candidate_root=candidate_root,
        base_overlay=base_overlay,
        step=1,
    )
    assert (overlay / "SKILL-addendum.md").is_file()
    assert isinstance(meta, MutatorMeta)
    assert meta.candidate_name == "step-001"
    assert meta.step == 1


def test_propose_rejects_bad_name() -> None:
    mutator = Mutator.new(
        provider=MockProvider(),
        skill_root=Path("/tmp/skillopt-x-skill"),
        candidate_root=Path("/tmp/skillopt-x-cand"),
        base_overlay=Path("/tmp/skillopt-x-base"),
    )
    with pytest.raises(MutatorError) as info:
        mutator._safe_name("bad name with spaces")
    assert info.value.code == "bad_name"
    with pytest.raises(MutatorError) as info2:
        mutator._safe_name("baseline")
    assert info2.value.code == "bad_name"


def test_propose_rejects_too_long(tmp_path: Path) -> None:
    skill_root, candidate_root, base_overlay = _setup_dirs(tmp_path)
    provider = MockProvider()
    long_addendum = "x" * _LONG_ADDENDUM_CHARS
    _scripted(provider, {"addendum": long_addendum, "reasoning": ""})
    with pytest.raises(MutatorError) as info:
        propose(
            provider=provider,
            skill_root=skill_root,
            candidate_root=candidate_root,
            base_overlay=base_overlay,
            step=1,
            max_addendum_chars=_MAX_ADDENDUM_CHARS,
        )
    assert info.value.code == "too_long"


def test_propose_rejects_forbidden_token(tmp_path: Path) -> None:
    skill_root, candidate_root, base_overlay = _setup_dirs(tmp_path)
    provider = MockProvider()
    _scripted(provider, {"addendum": "never use unwrap in this skill bundle", "reasoning": ""})
    with pytest.raises(MutatorError) as info:
        propose(
            provider=provider,
            skill_root=skill_root,
            candidate_root=candidate_root,
            base_overlay=base_overlay,
            step=1,
        )
    assert info.value.code == "forbidden"


def test_propose_reuses_candidate_root_path(tmp_path: Path) -> None:
    skill_root, candidate_root, base_overlay = _setup_dirs(tmp_path)
    provider = MockProvider()
    _scripted(provider, {"addendum": _SAFE_ADDENDUM, "reasoning": ""})
    _scripted(provider, {"addendum": _SAFE_ADDENDUM_TWO, "reasoning": ""})
    propose(
        provider=provider,
        skill_root=skill_root,
        candidate_root=candidate_root,
        base_overlay=base_overlay,
        step=1,
    )
    propose(
        provider=provider,
        skill_root=skill_root,
        candidate_root=candidate_root,
        base_overlay=base_overlay,
        step=2,
    )
    assert (candidate_root / "step-001" / "SKILL-addendum.md").is_file()
    assert (candidate_root / "step-002" / "SKILL-addendum.md").is_file()
