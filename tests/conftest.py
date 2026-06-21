from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def skill_tree(tmp_path: Path) -> Iterator[tuple[Path, Path, Path]]:
    skill_root = tmp_path / "skill"
    candidate_root = tmp_path / "candidates"
    base_overlay = tmp_path / "overlay"
    skill_root.mkdir()
    base_overlay.mkdir()
    (skill_root / "SKILL.md").write_text("# base skill\n", encoding="utf-8")
    yield skill_root, candidate_root, base_overlay
