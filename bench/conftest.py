from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Final, cast

import pytest

LARGE_COUNT: Final[int] = 50


def _make_skill_dir(root: Path, name: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (skill_dir / "rubric.json").write_text(
        json.dumps({"name": name, "forbidden_tokens": {"unsafe": "forbidden:unsafe"}}) + "\n",
        encoding="utf-8",
    )
    (skill_dir / "prompt.md").write_text(f"Hello {name}\n", encoding="utf-8")
    (skill_dir / "tasks.jsonl").write_text('{"id": "t1"}\n', encoding="utf-8")
    (skill_dir / "eval.py").write_text(
        "def run_eval(c, t, r): return {}\n", encoding="utf-8",
    )


def _raw_skills_root_large(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = cast(Path, tmp_path_factory.mktemp("skills_large"))
    for i in range(LARGE_COUNT):
        _make_skill_dir(root, f"skill-{i:03d}")
    return root


skills_root_large: Callable[..., Path] = pytest.fixture(scope="session")(_raw_skills_root_large)
