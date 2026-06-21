from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .errors import ConfigError
from .rubric import Rubric

_SKILL_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

REQUIRED_FILES: Final[tuple[str, ...]] = (
    "SKILL.md",
    "rubric.json",
    "prompt.md",
    "tasks.jsonl",
)


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    path: Path
    skill_md: Path
    eval_module: Path | None
    eval_script: Path | None
    prompt_path: Path
    tasks_path: Path
    config_path: Path | None
    references_dir: Path | None
    rubric: Rubric

    @staticmethod
    def from_path(skill_path: Path) -> Skill:
        for required in REQUIRED_FILES:
            target = skill_path / required
            if not target.is_file():
                raise ConfigError(
                    f"skill bundle missing {required}: {skill_path}",
                    code="skill_incomplete",
                    context={"missing": required, "path": str(skill_path)},
                )
        eval_py = skill_path / "eval.py"
        eval_sh = skill_path / "eval.sh"
        eval_module: Path | None = eval_py if eval_py.is_file() else None
        eval_script: Path | None = eval_sh if eval_sh.is_file() else None
        match (eval_module, eval_script):
            case (None, None):
                raise ConfigError(
                    f"skill bundle missing eval script (need eval.py or eval.sh): {skill_path}",
                    code="skill_no_eval",
                    context={"path": str(skill_path)},
                )
            case _:
                pass
        config_path = skill_path / "config.json"
        references_dir = skill_path / "references"
        return Skill(
            name=skill_path.name,
            path=skill_path,
            skill_md=skill_path / "SKILL.md",
            eval_module=eval_module,
            eval_script=eval_script,
            prompt_path=skill_path / "prompt.md",
            tasks_path=skill_path / "tasks.jsonl",
            config_path=config_path if config_path.is_file() else None,
            references_dir=references_dir if references_dir.is_dir() else None,
            rubric=Rubric.from_path(skill_path / "rubric.json"),
        )

    @staticmethod
    def find(skills_root: Path, skill_name: str) -> Skill:
        if not skills_root.is_dir():
            raise ConfigError(
                f"skills root not found: {skills_root}",
                code="skills_root_missing",
                context={"path": str(skills_root)},
            )
        if not _SKILL_NAME_RE.fullmatch(skill_name):
            raise ConfigError(
                f"invalid skill name: {skill_name!r}",
                code="skill_name_invalid",
                context={"name": skill_name},
            )
        skill_path = skills_root / skill_name
        if not skill_path.is_dir():
            raise ConfigError(
                f"skill not found: {skill_name}",
                code="skill_not_found",
                context={"name": skill_name, "path": str(skill_path)},
            )
        return Skill.from_path(skill_path)

    @staticmethod
    def discover(skills_root: Path) -> tuple[Skill, ...]:
        if not skills_root.is_dir():
            return ()
        out: list[Skill] = []
        for entry in sorted(skills_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue
            try:
                out.append(Skill.from_path(entry))
            except ConfigError:
                continue
        return tuple(out)

    def load_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")

    def load_default_config(self) -> Mapping[str, object]:
        match self.config_path:
            case Path() as p:
                try:
                    raw = json.loads(p.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    return {}
                match raw:
                    case dict() as d:
                        return d
                    case _:
                        return {}
            case _:
                return {}


__all__ = ["REQUIRED_FILES", "Skill"]
